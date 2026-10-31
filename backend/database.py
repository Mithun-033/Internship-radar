"""
SQLite database layer for Internship Radar.
Provides schema initialization, transaction handling, WAL mode, deduplication, and query helpers.
"""
import sqlite3
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import DB_PATH, APP_TIMEZONE, DEFAULT_SOURCES

logger = logging.getLogger("internship_radar.database")

def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with dict-like row factory and WAL mode enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes database schema and populates default source registry."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Listings table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT PRIMARY KEY,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            normalized_title TEXT NOT NULL,
            canonical_url TEXT NOT NULL,
            original_url TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_name TEXT NOT NULL,
            locations TEXT DEFAULT '[]',
            work_mode TEXT DEFAULT 'Unknown',
            date_posted_utc TEXT,
            date_posted_ist TEXT,
            is_today_ist INTEGER DEFAULT 0,
            date_verification_status TEXT DEFAULT 'unverified',
            date_source_evidence TEXT DEFAULT '',
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            degrees_allowed TEXT DEFAULT '[]',
            sponsorship_status TEXT DEFAULT 'Unspecified',
            eligibility_status TEXT NOT NULL,
            eligibility_reasons TEXT DEFAULT '[]',
            match_score INTEGER DEFAULT 0,
            match_category TEXT DEFAULT 'General Engineering',
            match_reasons TEXT DEFAULT '[]',
            matched_skills TEXT DEFAULT '[]',
            matched_projects TEXT DEFAULT '[]',
            missing_skills TEXT DEFAULT '[]',
            compensation TEXT DEFAULT '',
            deadline TEXT DEFAULT '',
            description_snippet TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            user_saved INTEGER DEFAULT 0,
            user_status TEXT DEFAULT 'none',
            user_notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)

        # Indexes for fast querying & daily feed filtering
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_date_ist ON listings(date_posted_ist);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_is_today ON listings(is_today_ist);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_eligibility ON listings(eligibility_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_match_score ON listings(match_score);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_company ON listings(company);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_user_status ON listings(user_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_canonical_url ON listings(canonical_url);")

        # Source registry table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            url TEXT,
            board_token TEXT,
            company TEXT,
            enabled INTEGER DEFAULT 1,
            interval_minutes INTEGER DEFAULT 30,
            last_checked_at TEXT,
            last_success_at TEXT,
            status TEXT DEFAULT 'pending',
            error_message TEXT DEFAULT '',
            items_indexed_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)

        # Collection runs history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS collection_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            sources_attempted INTEGER DEFAULT 0,
            sources_succeeded INTEGER DEFAULT 0,
            new_today_found INTEGER DEFAULT 0,
            total_listings_updated INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running',
            details TEXT DEFAULT ''
        );
        """)

        # Sync default sources into registry
        now_iso = datetime.now(timezone.utc).isoformat()
        for src in DEFAULT_SOURCES:
            cursor.execute("""
            INSERT INTO sources (id, name, type, url, board_token, company, enabled, interval_minutes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                type=excluded.type,
                url=excluded.url,
                board_token=excluded.board_token,
                company=excluded.company;
            """, (
                src["id"],
                src["name"],
                src["type"],
                src.get("url"),
                src.get("board_token"),
                src.get("company"),
                1 if src.get("enabled", True) else 0,
                src.get("interval_minutes", 30),
                now_iso,
                now_iso
            ))

        conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        conn.close()

def update_daily_flags(today_ist_str: str):
    """
    Recalculates the is_today_ist flag for all listings based on the current date in Asia/Kolkata.
    This guarantees daily rollover accuracy.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE listings
        SET is_today_ist = CASE
            WHEN date_posted_ist = ? AND date_verification_status = 'confirmed' THEN 1
            ELSE 0
        END;
        """, (today_ist_str,))
        conn.commit()
    finally:
        conn.close()

def upsert_listing(listing_data: Dict[str, Any]) -> bool:
    """
    Inserts or updates a listing.
    Preserves user_saved, user_status, user_notes, and first_seen_at if existing.
    Returns True if listing was inserted fresh, False if updated.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Check if listing exists
        cursor.execute("SELECT id, first_seen_at, user_saved, user_status, user_notes FROM listings WHERE id = ?", (listing_data["id"],))
        existing = cursor.fetchone()

        locations_json = json.dumps(listing_data.get("locations", []))
        degrees_json = json.dumps(listing_data.get("degrees_allowed", []))
        elig_reasons_json = json.dumps(listing_data.get("eligibility_reasons", []))
        match_reasons_json = json.dumps(listing_data.get("match_reasons", []))
        matched_skills_json = json.dumps(listing_data.get("matched_skills", []))
        matched_projects_json = json.dumps(listing_data.get("matched_projects", []))
        missing_skills_json = json.dumps(listing_data.get("missing_skills", []))

        if existing:
            first_seen = existing["first_seen_at"]
            user_saved = existing["user_saved"]
            user_status = existing["user_status"]
            user_notes = existing["user_notes"]
            is_new = False
        else:
            first_seen = listing_data.get("first_seen_at") or now_iso
            user_saved = listing_data.get("user_saved", 0)
            user_status = listing_data.get("user_status", "none")
            user_notes = listing_data.get("user_notes", "")
            is_new = True

        cursor.execute("""
        INSERT INTO listings (
            id, company, title, normalized_title, canonical_url, original_url,
            source_id, source_name, locations, work_mode, date_posted_utc,
            date_posted_ist, is_today_ist, date_verification_status,
            date_source_evidence, first_seen_at, last_seen_at, degrees_allowed,
            sponsorship_status, eligibility_status, eligibility_reasons,
            match_score, match_category, match_reasons, matched_skills,
            matched_projects, missing_skills, compensation, deadline,
            description_snippet, is_active, user_saved, user_status, user_notes,
            created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?
        ) ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            canonical_url=excluded.canonical_url,
            original_url=excluded.original_url,
            source_id=excluded.source_id,
            source_name=excluded.source_name,
            locations=excluded.locations,
            work_mode=excluded.work_mode,
            date_posted_utc=excluded.date_posted_utc,
            date_posted_ist=excluded.date_posted_ist,
            is_today_ist=excluded.is_today_ist,
            date_verification_status=excluded.date_verification_status,
            date_source_evidence=excluded.date_source_evidence,
            last_seen_at=excluded.last_seen_at,
            degrees_allowed=excluded.degrees_allowed,
            sponsorship_status=excluded.sponsorship_status,
            eligibility_status=excluded.eligibility_status,
            eligibility_reasons=excluded.eligibility_reasons,
            match_score=excluded.match_score,
            match_category=excluded.match_category,
            match_reasons=excluded.match_reasons,
            matched_skills=excluded.matched_skills,
            matched_projects=excluded.matched_projects,
            missing_skills=excluded.missing_skills,
            compensation=excluded.compensation,
            deadline=excluded.deadline,
            description_snippet=excluded.description_snippet,
            is_active=excluded.is_active,
            updated_at=excluded.updated_at;
        """, (
            listing_data["id"],
            listing_data["company"],
            listing_data["title"],
            listing_data.get("normalized_title", listing_data["title"].lower().strip()),
            listing_data["canonical_url"],
            listing_data.get("original_url", listing_data["canonical_url"]),
            listing_data["source_id"],
            listing_data["source_name"],
            locations_json,
            listing_data.get("work_mode", "Unknown"),
            listing_data.get("date_posted_utc"),
            listing_data.get("date_posted_ist"),
            1 if listing_data.get("is_today_ist") else 0,
            listing_data.get("date_verification_status", "unverified"),
            listing_data.get("date_source_evidence", ""),
            first_seen,
            listing_data.get("last_seen_at") or now_iso,
            degrees_json,
            listing_data.get("sponsorship_status", "Unspecified"),
            listing_data["eligibility_status"],
            elig_reasons_json,
            listing_data.get("match_score", 0),
            listing_data.get("match_category", "General Engineering"),
            match_reasons_json,
            matched_skills_json,
            matched_projects_json,
            missing_skills_json,
            listing_data.get("compensation", ""),
            listing_data.get("deadline", ""),
            listing_data.get("description_snippet", ""),
            1 if listing_data.get("is_active", True) else 0,
            user_saved,
            user_status,
            user_notes,
            first_seen,
            now_iso
        ))
        conn.commit()
        return is_new
    finally:
        conn.close()

def update_source_status(source_id: str, status: str, items_count: int = 0, error: str = ""):
    """Updates source health, last check, and count."""
    conn = get_connection()
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor = conn.cursor()
        if status == "healthy":
            cursor.execute("""
            UPDATE sources
            SET status = ?, last_checked_at = ?, last_success_at = ?, items_indexed_count = ?, error_message = '', updated_at = ?
            WHERE id = ?;
            """, (status, now_iso, now_iso, items_count, now_iso, source_id))
        else:
            cursor.execute("""
            UPDATE sources
            SET status = ?, last_checked_at = ?, error_message = ?, updated_at = ?
            WHERE id = ?;
            """, (status, now_iso, error, now_iso, source_id))
        conn.commit()
    finally:
        conn.close()

def get_stats(today_ist_str: str) -> Dict[str, Any]:
    """Computes real overview metrics from SQLite."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Today's verified feed count
        cursor.execute("SELECT COUNT(*) FROM listings WHERE is_today_ist = 1 AND is_active = 1 AND eligibility_status != 'ineligible';")
        today_count = cursor.fetchone()[0]

        # Last 7 Days count (Asia/Kolkata date math)
        cursor.execute("SELECT COUNT(*) FROM listings WHERE date_posted_ist >= date(?, '-7 days') AND is_active = 1 AND eligibility_status != 'ineligible';", (today_ist_str,))
        last7_count = cursor.fetchone()[0]

        # Strong matches (score >= 80)
        cursor.execute("SELECT COUNT(*) FROM listings WHERE match_score >= 80 AND is_active = 1 AND eligibility_status != 'ineligible';")
        strong_matches_count = cursor.fetchone()[0]

        # Eligible undergraduate
        cursor.execute("SELECT COUNT(*) FROM listings WHERE eligibility_status = 'eligible' AND is_active = 1;")
        eligible_count = cursor.fetchone()[0]

        # High priority roles (GPU / Triton / LLM Research / ML Systems with score >= 75)
        cursor.execute("""
        SELECT COUNT(*) FROM listings 
        WHERE match_score >= 75 
          AND match_category IN ('GPU & Triton Optimization', 'LLM Research & Modeling', 'ML Systems & Training Infra')
          AND is_active = 1
          AND eligibility_status != 'ineligible';
        """)
        high_priority_count = cursor.fetchone()[0]

        # Total open / indexed
        cursor.execute("SELECT COUNT(*) FROM listings WHERE is_active = 1 AND eligibility_status != 'ineligible';")
        total_open_count = cursor.fetchone()[0]

        # Saved count
        cursor.execute("SELECT COUNT(*) FROM listings WHERE user_saved = 1 AND eligibility_status != 'ineligible';")
        saved_count = cursor.fetchone()[0]

        # Applied / Tracked count (excluding dismissed/archived)
        cursor.execute("SELECT COUNT(*) FROM listings WHERE user_status NOT IN ('none', 'dismissed');")
        applied_count = cursor.fetchone()[0]

        # Archived / Dismissed count
        cursor.execute("SELECT COUNT(*) FROM listings WHERE user_status = 'dismissed';")
        archived_count = cursor.fetchone()[0]

        # Sources summary
        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END), SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) FROM sources WHERE enabled = 1;")
        total_sources, healthy_sources, error_sources = cursor.fetchone()

        # Category breakdowns for Today, Last 7 Days, and All
        cursor.execute("SELECT match_category, COUNT(*) FROM listings WHERE is_today_ist = 1 AND is_active = 1 AND eligibility_status != 'ineligible' GROUP BY match_category;")
        today_cats = dict(cursor.fetchall())

        cursor.execute("SELECT match_category, COUNT(*) FROM listings WHERE date_posted_ist >= date(?, '-7 days') AND is_active = 1 AND eligibility_status != 'ineligible' GROUP BY match_category;", (today_ist_str,))
        last7_cats = dict(cursor.fetchall())

        cursor.execute("SELECT match_category, COUNT(*) FROM listings WHERE is_active = 1 AND eligibility_status != 'ineligible' GROUP BY match_category;")
        all_cats = dict(cursor.fetchall())

        # Specific keyword counts for quick filters
        def get_kw_counts(where_clause, params_list):
            q = f"""SELECT 
                SUM(CASE WHEN LOWER(title) LIKE '%triton%' OR LOWER(title) LIKE '%gpu%' OR LOWER(matched_skills) LIKE '%triton%' OR LOWER(matched_skills) LIKE '%cuda%' OR match_category = 'GPU & Triton Optimization' THEN 1 ELSE 0 END),
                SUM(CASE WHEN LOWER(title) LIKE '%llm%' OR LOWER(title) LIKE '%language model%' OR LOWER(title) LIKE '%transformer%' OR match_category = 'LLM Research & Modeling' THEN 1 ELSE 0 END),
                SUM(CASE WHEN (
                    (LOWER(locations) LIKE '%india%' OR LOWER(locations) LIKE '%bangalore%' OR LOWER(locations) LIKE '%bengaluru%' 
                     OR LOWER(locations) LIKE '%hyderabad%' OR LOWER(locations) LIKE '%pune%' OR LOWER(locations) LIKE '%mumbai%' 
                     OR LOWER(locations) LIKE '%delhi%' OR LOWER(locations) LIKE '%noida%' OR LOWER(locations) LIKE '%gurgaon%' 
                     OR LOWER(locations) LIKE '%gurugram%' OR LOWER(locations) LIKE '%chennai%' OR LOWER(locations) LIKE '%trivandrum%' 
                     OR LOWER(locations) LIKE '%thiruvananthapuram%' OR LOWER(locations) LIKE '%kochi%' OR LOWER(locations) LIKE '%kolkata%')
                    AND LOWER(locations) NOT LIKE '%indiana%'
                    AND LOWER(locations) NOT LIKE '%indianapolis%'
                ) THEN 1 ELSE 0 END),
                SUM(CASE WHEN LOWER(work_mode) = 'remote' OR LOWER(locations) LIKE '%remote%' THEN 1 ELSE 0 END),
                SUM(CASE WHEN LOWER(title) LIKE '%2027%' OR LOWER(description_snippet) LIKE '%2027%' THEN 1 ELSE 0 END)
            FROM listings WHERE is_active = 1 AND eligibility_status != 'ineligible' AND {where_clause}"""
            cursor.execute(q, params_list)
            row = cursor.fetchone()
            return {
                "triton": row[0] or 0,
                "llm": row[1] or 0,
                "india": row[2] or 0,
                "remote": row[3] or 0,
                "summer2027": row[4] or 0
            }

        kw_today = get_kw_counts("is_today_ist = 1", [])
        kw_last7 = get_kw_counts("date_posted_ist >= date(?, '-7 days')", [today_ist_str])
        kw_all = get_kw_counts("1=1", [])

        return {
            "today_new_count": today_count,
            "last7_days_count": last7_count,
            "strong_matches_count": strong_matches_count,
            "eligible_count": eligible_count,
            "high_priority_count": high_priority_count,
            "total_open_count": total_open_count,
            "saved_count": saved_count,
            "applied_count": applied_count,
            "archived_count": archived_count,
            "sources_configured": total_sources or 0,
            "sources_healthy": healthy_sources or 0,
            "sources_error": error_sources or 0,
            "current_date_ist": today_ist_str,
            "category_counts": {
                "today": today_cats,
                "last7": last7_cats,
                "all": all_cats
            },
            "quick_filter_counts": {
                "today": kw_today,
                "last7": kw_last7,
                "all": kw_all
            }
        }
    finally:
        conn.close()

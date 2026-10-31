"""
FastAPI REST API routes.
Serves dashboard statistics, filtered feeds, bookmarks, source health, and data exports.
"""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import datetime
import json
import csv
import io

from .config import APP_TIMEZONE, CANDIDATE_PROFILE
from .database import get_connection, get_stats
from .scheduler import scheduler
from .collector import pipeline
from .eligibility import is_india_location

router = APIRouter(prefix="/api")

class StatusUpdateRequest(BaseModel):
    status: str # "none", "applied", "interviewing", "rejected", "dismissed"
    notes: Optional[str] = ""

class SaveToggleRequest(BaseModel):
    saved: bool

@router.get("/profile")
def get_candidate_profile():
    return CANDIDATE_PROFILE

@router.get("/stats")
def get_dashboard_stats():
    now_ist = datetime.datetime.now(APP_TIMEZONE)
    today_ist_str = now_ist.strftime("%Y-%m-%d")
    stats = get_stats(today_ist_str)
    stats["scheduler"] = scheduler.get_status()
    return stats

@router.get("/listings")
def list_listings(
    feed: str = Query("today", description="'today', 'all', 'saved', or 'applied'"),
    category: str = Query("all"),
    eligibility: str = Query("all"),
    min_score: int = Query(0, ge=0, le=100),
    work_mode: str = Query("all"),
    search: Optional[str] = Query(None),
    quick_filter: Optional[str] = Query(None, description="'triton', 'llm', 'india', 'remote', or 'summer2027'"),
    sort_by: str = Query("match"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    now_ist = datetime.datetime.now(APP_TIMEZONE)
    today_ist_str = now_ist.strftime("%Y-%m-%d")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        base_clauses = [
            "is_active = 1",
            "LOWER(title) NOT LIKE '%phd%'",
            "LOWER(title) NOT LIKE '%doctoral%'",
            "LOWER(title) NOT LIKE '%doctorate%'",
            "LOWER(title) NOT LIKE '%master%'",
            "LOWER(title) NOT LIKE '%postdoc%'",
            "LOWER(title) NOT LIKE '%mba%'",
            "LOWER(title) NOT LIKE '%associate intern%'",
            "LOWER(title) NOT LIKE '%student researcher%'",
            "LOWER(title) NOT LIKE '%graduate research%'",
            "LOWER(title) NOT LIKE '%graduate assistant%'",
            "LOWER(title) NOT LIKE '%m1/m2%'",
            "(degrees_allowed IS NULL OR degrees_allowed = '[]' OR LOWER(degrees_allowed) LIKE '%bachelor%' OR LOWER(degrees_allowed) LIKE '%undergrad%' OR LOWER(degrees_allowed) LIKE '%b.tech%' OR LOWER(degrees_allowed) LIKE '%associate%')",
            "NOT (LOWER(title) NOT LIKE '%intern%' AND LOWER(title) NOT LIKE '%student%' AND LOWER(title) NOT LIKE '%fellow%' AND LOWER(title) NOT LIKE '%co-op%' AND (LOWER(title) LIKE '%senior%' OR LOWER(title) LIKE '%staff%' OR LOWER(title) LIKE '%principal%'))",
            """(
                LOWER(title) LIKE '%intern%' OR 
                LOWER(title) LIKE '%co-op%' OR 
                LOWER(title) LIKE '%coop%' OR 
                LOWER(title) LIKE '%fellow%' OR 
                LOWER(title) LIKE '%trainee%' OR 
                LOWER(title) LIKE '%apprentice%' OR 
                LOWER(title) LIKE '%student%' OR 
                LOWER(title) LIKE '%placement%' OR
                LOWER(title) LIKE '%ntern%' OR
                LOWER(title) LIKE '%stagiaire%' OR
                LOWER(title) LIKE '%stagiere%' OR
                LOWER(title) LIKE '%practicum%' OR
                LOWER(title) LIKE '%resident%' OR
                LOWER(title) LIKE '%residency%' OR
                LOWER(title) LIKE '%scholar%' OR
                LOWER(title) LIKE '%summer analyst%' OR
                LOWER(title) LIKE '%summer associate%' OR
                LOWER(description_snippet) LIKE '%internship%' OR
                LOWER(description_snippet) LIKE '%undergraduate research%'
            )""",
            "LOWER(title) NOT LIKE '%full-time%'",
            "LOWER(title) NOT LIKE '%full time%'"
        ]
        base_params = []

        # Preset Quick Filter Constraints (exact match with telemetry widget counts)
        if quick_filter and quick_filter.strip():
            qf = quick_filter.lower().strip()
            if qf in ["triton", "gpu"]:
                base_clauses.append("(LOWER(title) LIKE '%triton%' OR LOWER(title) LIKE '%gpu%' OR LOWER(matched_skills) LIKE '%triton%' OR LOWER(matched_skills) LIKE '%cuda%' OR match_category = 'GPU & Triton Optimization')")
            elif qf in ["llm"]:
                base_clauses.append("(LOWER(title) LIKE '%llm%' OR LOWER(title) LIKE '%language model%' OR LOWER(title) LIKE '%transformer%' OR match_category = 'LLM Research & Modeling')")
            elif qf in ["india"]:
                base_clauses.append("""(
                    (LOWER(locations) LIKE '%india%' OR LOWER(locations) LIKE '%bangalore%' OR LOWER(locations) LIKE '%bengaluru%' 
                     OR LOWER(locations) LIKE '%hyderabad%' OR LOWER(locations) LIKE '%pune%' OR LOWER(locations) LIKE '%mumbai%' 
                     OR LOWER(locations) LIKE '%delhi%' OR LOWER(locations) LIKE '%noida%' OR LOWER(locations) LIKE '%gurgaon%' 
                     OR LOWER(locations) LIKE '%gurugram%' OR LOWER(locations) LIKE '%chennai%' OR LOWER(locations) LIKE '%trivandrum%' 
                     OR LOWER(locations) LIKE '%thiruvananthapuram%' OR LOWER(locations) LIKE '%kochi%' OR LOWER(locations) LIKE '%kolkata%')
                    AND LOWER(locations) NOT LIKE '%indiana%'
                    AND LOWER(locations) NOT LIKE '%indianapolis%'
                )""")
            elif qf in ["remote"]:
                base_clauses.append("(LOWER(work_mode) = 'remote' OR LOWER(locations) LIKE '%remote%')")
            elif qf in ["summer2027", "2027"]:
                base_clauses.append("(LOWER(title) LIKE '%2027%' OR LOWER(description_snippet) LIKE '%2027%')")

        # Category filter (flexible matching)
        if category != "all":
            if "gpu" in category.lower() or "triton" in category.lower():
                base_clauses.append("match_category = 'GPU & Triton Optimization'")
            elif "llm" in category.lower():
                base_clauses.append("match_category = 'LLM Research & Modeling'")
            elif "systems" in category.lower() and "ml" in category.lower():
                base_clauses.append("match_category = 'ML Systems & Training Infra'")
            elif "applied" in category.lower():
                base_clauses.append("match_category = 'Applied AI / ML'")
            elif "backend" in category.lower():
                base_clauses.append("match_category = 'Backend & Systems'")
            else:
                base_clauses.append("match_category = ?")
                base_params.append(category)

        # Eligibility filter
        if eligibility != "all":
            base_clauses.append("eligibility_status = ?")
            base_params.append(eligibility)
        else:
            # Default: show only eligible or potentially eligible undergrad opportunities
            base_clauses.append("eligibility_status != 'ineligible'")

        # Work mode filter
        if work_mode != "all":
            base_clauses.append("LOWER(work_mode) = ?")
            base_params.append(work_mode.lower())

        # Min score filter
        if min_score > 0:
            base_clauses.append("match_score >= ?")
            base_params.append(min_score)

        # Tokenized resilient search
        if search and search.strip():
            tokens = [t.strip().lower() for t in search.split() if t.strip()]
            for tok in tokens:
                kw = f"%{tok}%"
                base_clauses.append("(LOWER(title) LIKE ? OR LOWER(company) LIKE ? OR LOWER(description_snippet) LIKE ? OR LOWER(matched_skills) LIKE ? OR LOWER(matched_projects) LIKE ? OR LOWER(locations) LIKE ? OR LOWER(match_category) LIKE ?)")
                base_params.extend([kw, kw, kw, kw, kw, kw, kw])

        # Exclude dismissed if not specifically viewing archived tab
        if feed != "archived":
            base_clauses.append("user_status != 'dismissed'")

        # Feed type constraint
        feed_clauses = list(base_clauses)
        feed_params = list(base_params)

        if feed == "today":
            feed_clauses.append("is_today_ist = 1")
        elif feed == "last7":
            feed_clauses.append("date_posted_ist >= date(?, '-7 days')")
            feed_params.append(today_ist_str)
        elif feed == "saved":
            feed_clauses.append("user_saved = 1")
        elif feed == "applied":
            feed_clauses.append("user_status NOT IN ('none', 'dismissed')")
        elif feed == "archived":
            feed_clauses.append("user_status = 'dismissed'")

        where_sql = " AND ".join(feed_clauses)
        query = f"SELECT * FROM listings WHERE {where_sql}"

        # Sort order
        if sort_by == "match":
            sort_sql = " ORDER BY match_score DESC, date_posted_utc DESC"
        elif sort_by == "newest":
            sort_sql = " ORDER BY date_posted_utc DESC, match_score DESC"
        elif sort_by == "company":
            sort_sql = " ORDER BY company ASC, match_score DESC"
        elif sort_by == "title":
            sort_sql = " ORDER BY title ASC"
        else:
            sort_sql = " ORDER BY match_score DESC"

        # Count total matching query before pagination
        count_query = f"SELECT COUNT(*) FROM listings WHERE {where_sql}"
        cursor.execute(count_query, feed_params)
        total_matching = cursor.fetchone()[0]

        # Apply pagination
        paginated_query = f"{query}{sort_sql} LIMIT ? OFFSET ?"
        exec_params = feed_params + [limit, offset]

        cursor.execute(paginated_query, exec_params)
        rows = cursor.fetchall()

        listings = []
        for r in rows:
            d = dict(r)
            # Deserialize JSON fields
            for f in ["locations", "degrees_allowed", "eligibility_reasons", "match_reasons", "matched_skills", "matched_projects", "missing_skills"]:
                if d.get(f):
                    try:
                        d[f] = json.loads(d[f])
                    except:
                        d[f] = []
                else:
                    d[f] = []
            locs = d.get("locations") or []
            d["is_india"] = any(is_india_location(l) for l in locs)
            listings.append(d)

        fallback_counts = None
        if total_matching == 0 and feed == "today" and (search or category != "all" or quick_filter):
            # Check how many exist in Last 7 Days and All Catalog
            base_where = " AND ".join(base_clauses)
            try:
                cursor.execute(f"SELECT COUNT(*) FROM listings WHERE date_posted_ist >= date(?, '-7 days') AND {base_where}", [today_ist_str] + base_params)
                last7_hits = cursor.fetchone()[0]
            except Exception:
                last7_hits = 0

            try:
                cursor.execute(f"SELECT COUNT(*) FROM listings WHERE {base_where}", base_params)
                all_hits = cursor.fetchone()[0]
            except Exception:
                all_hits = 0

            fallback_counts = {
                "last7": last7_hits,
                "all": all_hits
            }

        return {
            "total": total_matching,
            "feed": feed,
            "today_ist": today_ist_str,
            "limit": limit,
            "offset": offset,
            "fallback": fallback_counts,
            "listings": listings
        }
    finally:
        conn.close()

@router.get("/listings/{listing_id}")
def get_listing(listing_id: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Listing not found")
        d = dict(row)
        for f in ["locations", "degrees_allowed", "eligibility_reasons", "match_reasons", "matched_skills", "matched_projects", "missing_skills"]:
            if d.get(f):
                try:
                    d[f] = json.loads(d[f])
                except:
                    d[f] = []
            else:
                d[f] = []
        locs = d.get("locations") or []
        d["is_india"] = any(is_india_location(l) for l in locs)
        return d
    finally:
        conn.close()

@router.post("/listings/{listing_id}/save")
def toggle_save_listing(listing_id: str, body: SaveToggleRequest):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE listings SET user_saved = ? WHERE id = ?", (1 if body.saved else 0, listing_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Listing not found")
        conn.commit()
        return {"id": listing_id, "saved": body.saved}
    finally:
        conn.close()

@router.post("/listings/{listing_id}/status")
def update_listing_status(listing_id: str, body: StatusUpdateRequest):
    valid_statuses = {"none", "applied", "interviewing", "rejected", "dismissed"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE listings 
        SET user_status = ?, user_notes = ? 
        WHERE id = ?;
        """, (body.status, body.notes or "", listing_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Listing not found")
        conn.commit()
        return {"id": listing_id, "status": body.status, "notes": body.notes}
    finally:
        conn.close()

@router.delete("/listings/{listing_id}/status")
def reset_listing_status(listing_id: str):
    """Manually removes an opportunity from Applied/Tracked pipeline."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE listings SET user_status = 'none', user_notes = '' WHERE id = ?", (listing_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Listing not found")
        conn.commit()
        return {"id": listing_id, "status": "none"}
    finally:
        conn.close()

@router.post("/listings/{listing_id}/archive")
def archive_listing(listing_id: str):
    """Archives/dismisses an opportunity so it is hidden from active feeds."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE listings SET user_status = 'dismissed' WHERE id = ?", (listing_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Listing not found")
        conn.commit()
        return {"id": listing_id, "status": "dismissed"}
    finally:
        conn.close()

@router.post("/listings/{listing_id}/unarchive")
def unarchive_listing(listing_id: str):
    """Restores an archived opportunity back into regular active feeds."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE listings SET user_status = 'none' WHERE id = ?", (listing_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Listing not found")
        conn.commit()
        return {"id": listing_id, "status": "none"}
    finally:
        conn.close()

@router.post("/listings/{listing_id}/pitch")
def generate_outreach_pitch(listing_id: str):
    """Generates a high-signal personalized outreach cold message based on the candidate's technical profile."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Listing not found")
        d = dict(row)
        comp = d["company"]
        title = d["title"]
        cat = d.get("match_category", "General Engineering")

        if cat == "GPU & Triton Optimization":
            pitch = (
                f"Hi team, I noticed your opening for {title} at {comp}. I'm a Computer Science undergraduate "
                f"(graduating 2029) specializing in GPU kernel engineering and Triton. Recently, I authored Triton MuonAdamW, "
                f"writing hand-tuned Triton kernels for Newton-Schulz orthogonalization and fused AdamW that outperform PyTorch's "
                f"built-in Muon by 1.27-1.30x. I'd love to contribute to {comp}'s accelerated compute initiatives."
            )
        elif cat == "LLM Research & Modeling":
            pitch = (
                f"Hi team, I saw the {title} opening at {comp}. I'm a Computer Science undergraduate (2029 grad) focusing "
                f"on language modeling research. I designed and pretrained PocketGPT, a 320M-parameter decoder-only Transformer "
                f"from scratch on ~5B ClimbMix tokens on a single H100 (featuring RoPE, RMSNorm, GQA, QK-Norm, and custom hybrid optimizers), "
                f"outperforming Pythia-410M on zero-shot ARC and OpenBookQA. I'd love to bring this pretraining rigor to {comp}."
            )
        elif cat == "ML Systems & Training Infra":
            pitch = (
                f"Hi team, I'm reaching out regarding {title} at {comp}. I'm a Computer Science undergraduate (class of 2029) "
                f"working at the intersection of deep learning training loops and GPU memory efficiency. My recent projects include "
                f"custom PyTorch Lightning distributed pipelines, memory-mapped data ingestion, and operator kernel fusion in Triton. "
                f"I'm eager to help scale {comp}'s ML infrastructure."
            )
        elif cat == "Applied AI / ML":
            pitch = (
                f"Hi team, I'm excited about the {title} position at {comp}. I'm a CS undergraduate (2029 grad, 9.15 CGPA) "
                f"with practical DL experience, including building a scratch ConvNeXt V2 classifier for the IJCAI-ECAI FREUID Challenge "
                f"with Optuna hyperparameter optimization and Docker containerized inference. I'd love to apply this modeling and systems "
                f"experience to {comp}'s machine learning team."
            )
        else:
            pitch = (
                f"Hi team, I'm writing to express interest in the {title} role at {comp}. I'm an undergraduate CSE student "
                f"(graduating 2029, 9.15 CGPA) with 450+ LeetCode problems solved across C++ and Python, plus hands-on experience in FastAPI, "
                f"Docker, and distributed computing. I would welcome the opportunity to contribute to {comp}'s engineering team."
            )

        return {
            "id": listing_id,
            "company": comp,
            "title": title,
            "category": cat,
            "pitch": pitch
        }
    finally:
        conn.close()

@router.get("/sources")
def list_sources():
    """Lists all configured source connectors and their live health status."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources ORDER BY status ASC, name ASC;")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.post("/sources/{source_id}/check")
def check_single_source(source_id: str):
    """Triggers an on-demand health scan of a single source connector."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources WHERE id = ?", (source_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Source not found")
        src_dict = dict(row)
        items_count = pipeline.run_source(src_dict)
        return {"id": source_id, "status": "healthy", "items_fetched": items_count}
    except Exception as e:
        return {"id": source_id, "status": "error", "error": str(e)}
    finally:
        conn.close()

@router.post("/sources/{source_id}/toggle")
def toggle_source(source_id: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT enabled FROM sources WHERE id = ?", (source_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Source not found")
        new_val = 0 if row["enabled"] == 1 else 1
        cursor.execute("UPDATE sources SET enabled = ? WHERE id = ?", (new_val, source_id))
        conn.commit()
        return {"id": source_id, "enabled": bool(new_val)}
    finally:
        conn.close()

@router.post("/refresh")
def trigger_refresh():
    scheduler.trigger_immediate_refresh()
    return {"message": "Immediate collection triggered across all enabled sources."}

@router.get("/export")
def export_data(format: str = Query("json", description="'json' or 'csv'"), feed: str = Query("all")):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM listings WHERE is_active = 1"
        if feed == "today":
            query += " AND is_today_ist = 1"
        elif feed == "saved":
            query += " AND user_saved = 1"
        elif feed == "applied":
            query += " AND user_status != 'none'"
        query += " ORDER BY match_score DESC"

        cursor.execute(query)
        rows = cursor.fetchall()
        items = []
        for r in rows:
            d = dict(r)
            for f in ["locations", "degrees_allowed", "eligibility_reasons", "match_reasons", "matched_skills", "matched_projects", "missing_skills"]:
                if d.get(f):
                    try:
                        d[f] = json.loads(d[f])
                    except:
                        d[f] = []
            items.append(d)

        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if format.lower() == "csv":
            output = io.StringIO()
            fieldnames = [
                "company", "title", "match_score", "match_category", "eligibility_status",
                "date_posted_ist", "work_mode", "locations", "canonical_url", "user_status"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for it in items:
                row_copy = it.copy()
                row_copy["locations"] = "; ".join(it.get("locations", []))
                writer.writerow(row_copy)
            csv_content = output.getvalue()
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=internships_{feed}_{now_str}.csv"}
            )
        else:
            return Response(
                content=json.dumps(items, indent=2),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=internships_{feed}_{now_str}.json"}
            )
    finally:
        conn.close()

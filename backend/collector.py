"""
Collection Orchestrator.
Executes multi-source data ingestion, updates health status,
and recalculates daily rollover flags in Asia/Kolkata timezone.
"""
from typing import List, Dict, Any, Optional
import datetime
import logging
import traceback

from .config import APP_TIMEZONE, DEFAULT_SOURCES
from .database import (
    get_connection, upsert_listing, update_source_status,
    update_daily_flags
)
from .eligibility import is_graduate_or_phd_role
from .connectors.live_feed import LiveFeedConnector
from .connectors.workday import WorkdayConnector
from .connectors.smartrecruiters import SmartRecruitersConnector
from .connectors.greenhouse import GreenhouseConnector
from .connectors.ashby import AshbyConnector
from .connectors.remote_rss import RemoteOKConnector, WWRConnector
from .connectors.india_internships import IndiaInternshipsConnector

logger = logging.getLogger("internship_radar.collector")

def get_connector_for_source(src_dict: Dict[str, Any]):
    """Factory creating connector instance based on source configuration."""
    stype = src_dict.get("type")
    sid = src_dict.get("id")
    name = src_dict.get("name")
    interval = src_dict.get("interval_minutes", 30)

    if stype == "live_feed":
        return LiveFeedConnector(sid, name, src_dict["url"], interval)
    elif stype == "workday":
        return WorkdayConnector(sid, name, src_dict["url"], src_dict.get("company", "NVIDIA"), interval)
    elif stype == "smartrecruiters":
        return SmartRecruitersConnector(sid, name, src_dict["url"], src_dict.get("company", "CERN"), interval)
    elif stype == "greenhouse":
        return GreenhouseConnector(sid, name, src_dict["board_token"], src_dict.get("company", "Tech"), interval)
    elif stype == "ashby":
        return AshbyConnector(sid, name, src_dict["board_token"], src_dict.get("company", "Startup"), interval)
    elif stype == "remoteok":
        return RemoteOKConnector(sid, name, src_dict.get("url", "https://remoteok.com/api"), interval)
    elif stype == "rss":
        return WWRConnector(sid, name, src_dict["url"], interval)
    elif stype == "india_feed":
        return IndiaInternshipsConnector(sid, name, interval)
    else:
        logger.warning(f"Unknown source type: {stype}")
        return None

class CollectionPipeline:
    def __init__(self):
        self.is_running = False

    def get_enabled_sources(self) -> List[Dict[str, Any]]:
        """Retrieves enabled sources from SQLite registry."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sources WHERE enabled = 1;")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def run_source(self, src: Dict[str, Any]) -> int:
        """Executes collection for a single source, catches errors, and updates registry."""
        connector = get_connector_for_source(src)
        if not connector:
            return 0

        source_id = src["id"]
        logger.info(f"--- Running collection for source: {src['name']} ({source_id}) ---")
        try:
            listings = connector.fetch_listings()
            now_ist = datetime.datetime.now(APP_TIMEZONE)
            today_ist_str = now_ist.strftime("%Y-%m-%d")

            count = 0
            for item in listings:
                # Discard ANY PhD / Master's / Graduate roles immediately
                if is_graduate_or_phd_role(item.get("title", ""), item.get("description_snippet", ""), item.get("degrees_allowed", [])):
                    continue

                # Set is_today_ist based on confirmed date
                item["is_today_ist"] = (
                    item.get("date_posted_ist") == today_ist_str and 
                    item.get("date_verification_status") == "confirmed"
                )
                upsert_listing(item)
                count += 1

            update_source_status(source_id, "healthy", items_count=count)
            logger.info(f"Source {source_id} successfully updated with {count} listings.")
            return count
        except Exception as e:
            err_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Source {source_id} failed: {err_msg}")
            update_source_status(source_id, "error", error=err_msg)
            return 0

    def run_all(self) -> Dict[str, Any]:
        """Runs collection across all configured sources and records summary."""
        if self.is_running:
            logger.warning("Collection pipeline is already running. Skipping duplicate trigger.")
            return {"status": "already_running"}

        self.is_running = True
        started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        logger.info(f"Starting full collection cycle at {started_at}...")

        conn = get_connection()
        run_id = None
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO collection_runs (started_at, status) VALUES (?, 'running');", (started_at,))
            conn.commit()
            run_id = cursor.lastrowid
        finally:
            conn.close()

        sources = self.get_enabled_sources()
        sources_succeeded = 0
        total_items_updated = 0

        for src in sources:
            try:
                cnt = self.run_source(src)
                if cnt > 0:
                    sources_succeeded += 1
                    total_items_updated += cnt
            except Exception as e:
                logger.error(f"Unexpected crash running {src.get('id')}: {e}")

        # Recalculate daily flags in Asia/Kolkata
        now_ist = datetime.datetime.now(APP_TIMEZONE)
        today_ist_str = now_ist.strftime("%Y-%m-%d")
        update_daily_flags(today_ist_str)

        finished_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Count new today
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_today_ist = 1;")
            new_today_found = cursor.fetchone()[0]

            if run_id:
                cursor.execute("""
                UPDATE collection_runs
                SET finished_at = ?, sources_attempted = ?, sources_succeeded = ?,
                    new_today_found = ?, total_listings_updated = ?, status = 'completed',
                    details = ?
                WHERE id = ?;
                """, (
                    finished_at, len(sources), sources_succeeded,
                    new_today_found, total_items_updated,
                    f"Completed run across {len(sources)} sources. Found {new_today_found} new today.",
                    run_id
                ))
                conn.commit()
        finally:
            conn.close()

        self.is_running = False
        logger.info(f"Full collection cycle finished: {sources_succeeded}/{len(sources)} sources succeeded. {new_today_found} today's items active.")

        return {
            "status": "completed",
            "sources_attempted": len(sources),
            "sources_succeeded": sources_succeeded,
            "total_items_updated": total_items_updated,
            "new_today_found": new_today_found,
            "current_date_ist": today_ist_str
        }

# Global singleton pipeline instance
pipeline = CollectionPipeline()

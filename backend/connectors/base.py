"""
Base Source Connector interface.
Handles HTTP requests with timeouts, user-agent headers, rate limiting, and timezone conversion.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import requests
import datetime
import zoneinfo
import logging
import time

from ..config import APP_TIMEZONE, RATE_LIMIT_DELAY_SECONDS

logger = logging.getLogger("internship_radar.connector")

class BaseConnector(ABC):
    def __init__(self, source_id: str, name: str, interval_minutes: int = 30):
        self.source_id = source_id
        self.name = name
        self.interval_minutes = interval_minutes
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 InternshipRadar/1.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9"
        })

    @abstractmethod
    def fetch_listings(self) -> List[Dict[str, Any]]:
        """Fetches listings from the source and returns normalized listing dicts."""
        pass

    def parse_timestamp_to_ist(self, dt_val: Any) -> Optional[tuple[str, str, datetime.datetime]]:
        """
        Parses unix timestamp or ISO string into:
        (iso_utc_str, ist_date_str "YYYY-MM-DD", datetime_obj_ist)
        """
        if not dt_val:
            return None
        try:
            dt = None
            if isinstance(dt_val, (int, float)):
                # Handle milliseconds vs seconds
                if dt_val > 1e11:
                    dt_val = dt_val / 1000.0
                dt = datetime.datetime.fromtimestamp(dt_val, tz=datetime.timezone.utc)
            elif isinstance(dt_val, str):
                # Standard ISO parsing
                clean_str = dt_val.replace("Z", "+00:00")
                dt = datetime.datetime.fromisoformat(clean_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
            
            if dt:
                ist_dt = dt.astimezone(APP_TIMEZONE)
                iso_utc = dt.astimezone(datetime.timezone.utc).isoformat()
                date_ist_str = ist_dt.strftime("%Y-%m-%d")
                return (iso_utc, date_ist_str, ist_dt)
        except Exception as e:
            logger.debug(f"Failed to parse timestamp {dt_val}: {e}")
        return None

    def sleep_rate_limit(self):
        time.sleep(RATE_LIMIT_DELAY_SECONDS)

"""
Connector for Live Internship Repositories (SimplifyJobs Summer 2026/2027).
Tracks thousands of active, verified internship opportunities with exact timestamps.
"""
from typing import List, Dict, Any
import logging
from datetime import datetime

from .base import BaseConnector
from ..deduplication import clean_canonical_url, normalize_company, generate_listing_id
from ..eligibility import evaluate_eligibility
from ..matching import score_listing

logger = logging.getLogger("internship_radar.connectors.live_feed")

class LiveFeedConnector(BaseConnector):
    def __init__(self, source_id: str, name: str, url: str, interval_minutes: int = 30):
        super().__init__(source_id, name, interval_minutes)
        self.url = url

    def fetch_listings(self) -> List[Dict[str, Any]]:
        results = []
        try:
            logger.info(f"Fetching listings from {self.name} at {self.url}...")
            resp = self.session.get(self.url, timeout=15)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch {self.url}, status: {resp.status_code}")
                return results

            items = resp.json()
            logger.info(f"Received {len(items)} items from {self.name}. Processing active items...")

            for it in items:
                # We only want active opportunities
                if not it.get("active", False):
                    continue

                title = it.get("title", "").strip()
                company_raw = it.get("company_name", "").strip()
                if not title or not company_raw:
                    continue

                original_url = it.get("url", "").strip()
                canonical_url = clean_canonical_url(original_url)
                company = normalize_company(company_raw)

                # Date parsing
                dp = it.get("date_posted")
                date_tuple = self.parse_timestamp_to_ist(dp)
                
                if date_tuple:
                    date_utc, date_ist, dt_ist = date_tuple
                    date_status = "confirmed"
                    evidence = f"Verified repository posting timestamp: {dt_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC: {date_utc})"
                else:
                    date_utc = None
                    date_ist = None
                    date_status = "unverified"
                    evidence = "Original posting date not provided in source feed"

                locations = it.get("locations", [])
                if isinstance(locations, str):
                    locations = [locations]

                degrees = it.get("degrees", [])
                if isinstance(degrees, str):
                    degrees = [degrees]

                sponsorship = it.get("sponsorship", "Unspecified")
                category_raw = it.get("category", "")
                terms = it.get("terms", [])
                terms_str = ", ".join(terms) if terms else ""

                work_mode = "Remote" if any("remote" in str(loc).lower() for loc in locations) else "On-site"
                if any("hybrid" in str(loc).lower() for loc in locations):
                    work_mode = "Hybrid"

                listing_id = generate_listing_id(company, title, canonical_url)

                raw_listing = {
                    "id": listing_id,
                    "company": company,
                    "title": title,
                    "canonical_url": canonical_url,
                    "original_url": original_url,
                    "source_id": self.source_id,
                    "source_name": self.name,
                    "locations": locations,
                    "work_mode": work_mode,
                    "date_posted_utc": date_utc,
                    "date_posted_ist": date_ist,
                    "date_verification_status": date_status,
                    "date_source_evidence": evidence,
                    "degrees_allowed": degrees,
                    "sponsorship_status": sponsorship,
                    "description_snippet": f"Category: {category_raw}. Terms: {terms_str}. Location: {', '.join(locations)}.",
                    "deadline": ""
                }

                # Evaluate eligibility
                elig_status, elig_reasons = evaluate_eligibility(raw_listing)
                raw_listing["eligibility_status"] = elig_status
                raw_listing["eligibility_reasons"] = elig_reasons

                # Score relevance
                score, match_cat, match_reasons, matched_skills, matched_proj, missing_skills = score_listing(raw_listing)
                raw_listing["match_score"] = score
                raw_listing["match_category"] = match_cat
                raw_listing["match_reasons"] = match_reasons
                raw_listing["matched_skills"] = matched_skills
                raw_listing["matched_projects"] = matched_proj
                raw_listing["missing_skills"] = missing_skills

                results.append(raw_listing)

            logger.info(f"Successfully processed {len(results)} active listings from {self.name}.")
        except Exception as e:
            logger.error(f"Error fetching from {self.name}: {e}", exc_info=True)
            raise

        return results

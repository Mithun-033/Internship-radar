"""
Connector for Ashby ATS Job Boards.
Queries official Ashby job board APIs for frontier AI startups:
Perplexity AI, Cursor (Anysphere), Replit, etc.
"""
from typing import List, Dict, Any
import logging
import re

from .base import BaseConnector
from ..deduplication import clean_canonical_url, normalize_company, generate_listing_id
from ..eligibility import evaluate_eligibility
from ..matching import score_listing

logger = logging.getLogger("internship_radar.connectors.ashby")

INTERN_KEYWORDS = [
    "intern", "internship", "fellow", "fellowship", "student", "co-op", "coop", "apprentice", "trainee"
]

class AshbyConnector(BaseConnector):
    def __init__(self, source_id: str, name: str, board_token: str, company: str, interval_minutes: int = 30):
        super().__init__(source_id, name, interval_minutes)
        self.board_token = board_token
        self.company = company
        self.url = f"https://api.ashbyhq.com/posting-api/job-board/{board_token}"

    def fetch_listings(self) -> List[Dict[str, Any]]:
        results = []
        try:
            logger.info(f"Fetching Ashby jobs for {self.company} ({self.board_token})...")
            resp = self.session.get(self.url, timeout=12)
            if resp.status_code != 200:
                logger.error(f"Ashby fetch failed for {self.board_token}: status {resp.status_code}")
                return results

            data = resp.json()
            jobs = data.get("jobs", [])
            logger.info(f"Ashby {self.company} returned {len(jobs)} total jobs.")

            for job in jobs:
                title = job.get("title", "").strip()
                if not title:
                    continue

                lower_title = title.lower()
                is_target_role = any(re.search(rf'\b{k}\b', lower_title) for k in INTERN_KEYWORDS)
                if not is_target_role:
                    continue

                job_url = job.get("jobUrl")
                if not job_url:
                    continue

                canonical_url = clean_canonical_url(job_url)
                company_name = normalize_company(self.company)

                # Parse date
                published_at = job.get("publishedAt")
                date_tuple = self.parse_timestamp_to_ist(published_at)
                if date_tuple:
                    date_utc, date_ist, dt_ist = date_tuple
                    date_status = "confirmed"
                    evidence = f"Ashby verified official publishedAt timestamp: {dt_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC: {date_utc})"
                else:
                    date_utc, date_ist = None, None
                    date_status = "unverified"
                    evidence = "No verified date timestamp in Ashby record"

                location = job.get("location", "Unspecified")
                locations = [location] if location else ["Unspecified"]
                work_mode = "Remote" if "remote" in (location or "").lower() else "On-site"
                if "hybrid" in (location or "").lower():
                    work_mode = "Hybrid"

                dept = job.get("department", "")
                snippet = f"Department: {dept}. Location: {location}." if dept else f"Location: {location}."

                listing_id = generate_listing_id(company_name, title, canonical_url)

                raw_listing = {
                    "id": listing_id,
                    "company": company_name,
                    "title": title,
                    "canonical_url": canonical_url,
                    "original_url": job_url,
                    "source_id": self.source_id,
                    "source_name": self.name,
                    "locations": locations,
                    "work_mode": work_mode,
                    "date_posted_utc": date_utc,
                    "date_posted_ist": date_ist,
                    "date_verification_status": date_status,
                    "date_source_evidence": evidence,
                    "degrees_allowed": ["Bachelor's"] if "phd" not in lower_title else ["PhD"],
                    "sponsorship_status": "Official startup career board",
                    "description_snippet": snippet,
                    "deadline": ""
                }

                elig_status, elig_reasons = evaluate_eligibility(raw_listing)
                raw_listing["eligibility_status"] = elig_status
                raw_listing["eligibility_reasons"] = elig_reasons

                score, match_cat, match_reasons, matched_skills, matched_proj, missing_skills = score_listing(raw_listing)
                raw_listing["match_score"] = score
                raw_listing["match_category"] = match_cat
                raw_listing["match_reasons"] = match_reasons
                raw_listing["matched_skills"] = matched_skills
                raw_listing["matched_projects"] = matched_proj
                raw_listing["missing_skills"] = missing_skills

                results.append(raw_listing)

            logger.info(f"Processed {len(results)} relevant listings from Ashby {self.company}.")
        except Exception as e:
            logger.error(f"Error in Ashby connector {self.company}: {e}", exc_info=True)
            raise

        return results

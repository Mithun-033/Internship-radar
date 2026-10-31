"""
Connector for Greenhouse ATS Boards.
Queries official Greenhouse job board APIs for frontier AI & tech companies:
Anthropic, Scale AI, Databricks, Stripe, Cloudflare, Roblox, etc.
"""
from typing import List, Dict, Any
import logging
import re
from bs4 import BeautifulSoup

from .base import BaseConnector
from ..deduplication import clean_canonical_url, normalize_company, generate_listing_id
from ..eligibility import evaluate_eligibility
from ..matching import score_listing

logger = logging.getLogger("internship_radar.connectors.greenhouse")

INTERN_KEYWORDS = [
    "intern", "internship", "fellow", "fellowship", "student", "co-op", "coop", "apprentice", "trainee"
]

class GreenhouseConnector(BaseConnector):
    def __init__(self, source_id: str, name: str, board_token: str, company: str, interval_minutes: int = 30):
        super().__init__(source_id, name, interval_minutes)
        self.board_token = board_token
        self.company = company
        self.url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

    def fetch_listings(self) -> List[Dict[str, Any]]:
        results = []
        try:
            logger.info(f"Fetching Greenhouse jobs for {self.company} ({self.board_token})...")
            resp = self.session.get(self.url, timeout=15)
            if resp.status_code != 200:
                logger.error(f"Greenhouse fetch failed for {self.board_token}: status {resp.status_code}")
                return results

            data = resp.json()
            jobs = data.get("jobs", [])
            logger.info(f"Greenhouse {self.company} returned {len(jobs)} total jobs.")

            for job in jobs:
                title = job.get("title", "").strip()
                if not title:
                    continue

                lower_title = title.lower()
                # Check if it's an internship or early career/research role
                is_target_role = any(re.search(rf'\b{k}\b', lower_title) for k in INTERN_KEYWORDS)
                
                # If company is Anthropic, also look for Fellows, Residency, or Systems roles
                if not is_target_role:
                    continue

                abs_url = job.get("absolute_url")
                if not abs_url:
                    continue

                canonical_url = clean_canonical_url(abs_url)
                company_name = normalize_company(self.company)

                # Parse date
                updated_at = job.get("updated_at")
                date_tuple = self.parse_timestamp_to_ist(updated_at)
                if date_tuple:
                    date_utc, date_ist, dt_ist = date_tuple
                    date_status = "confirmed"
                    evidence = f"Greenhouse verified official posting timestamp: {dt_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC: {date_utc})"
                else:
                    date_utc, date_ist = None, None
                    date_status = "unverified"
                    evidence = "No verified date timestamp in Greenhouse record"

                # Extract location
                loc_obj = job.get("location", {})
                loc_name = loc_obj.get("name") if isinstance(loc_obj, dict) else str(loc_obj)
                locations = [loc_name] if loc_name else ["Unspecified"]
                work_mode = "Remote" if "remote" in (loc_name or "").lower() else "On-site"
                if "hybrid" in (loc_name or "").lower():
                    work_mode = "Hybrid"

                # Extract text snippet from HTML content
                raw_content = job.get("content", "")
                snippet = ""
                if raw_content:
                    soup = BeautifulSoup(raw_content, "html.parser")
                    clean_text = soup.get_text(" ", strip=True)
                    snippet = clean_text[:400] + "..." if len(clean_text) > 400 else clean_text

                listing_id = generate_listing_id(company_name, title, canonical_url)

                raw_listing = {
                    "id": listing_id,
                    "company": company_name,
                    "title": title,
                    "canonical_url": canonical_url,
                    "original_url": abs_url,
                    "source_id": self.source_id,
                    "source_name": self.name,
                    "locations": locations,
                    "work_mode": work_mode,
                    "date_posted_utc": date_utc,
                    "date_posted_ist": date_ist,
                    "date_verification_status": date_status,
                    "date_source_evidence": evidence,
                    "degrees_allowed": ["Bachelor's"] if "phd" not in lower_title else ["PhD"],
                    "sponsorship_status": "Official company career page listing",
                    "description_snippet": snippet or f"Official listing at {company_name}.",
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

            logger.info(f"Processed {len(results)} relevant listings from Greenhouse {self.company}.")
        except Exception as e:
            logger.error(f"Error in Greenhouse connector {self.company}: {e}", exc_info=True)
            raise

        return results

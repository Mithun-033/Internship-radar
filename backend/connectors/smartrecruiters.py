"""
Connector for SmartRecruiters (CERN openlab / Scientific Computing).
Tracks research, AI, distributed systems, and undergraduate engineering programs at CERN.
"""
from typing import List, Dict, Any
import logging
from datetime import datetime

from .base import BaseConnector
from ..deduplication import clean_canonical_url, normalize_company, generate_listing_id
from ..eligibility import evaluate_eligibility
from ..matching import score_listing

logger = logging.getLogger("internship_radar.connectors.smartrecruiters")

class SmartRecruitersConnector(BaseConnector):
    def __init__(self, source_id: str, name: str, url: str, company: str = "CERN", interval_minutes: int = 60):
        super().__init__(source_id, name, interval_minutes)
        self.url = url
        self.company = company

    def fetch_listings(self) -> List[Dict[str, Any]]:
        results = []
        try:
            logger.info(f"Fetching listings from SmartRecruiters for {self.company} at {self.url}...")
            resp = self.session.get(self.url, timeout=12)
            if resp.status_code != 200:
                logger.error(f"SmartRecruiters fetch failed for {self.company}: status {resp.status_code}")
                return results

            data = resp.json()
            postings = data.get("content", [])
            logger.info(f"Fetched {len(postings)} postings from {self.company} SmartRecruiters.")

            for post in postings:
                title = post.get("name", "").strip()
                post_id = post.get("id")
                ref_num = post.get("refNumber", "")
                released_date = post.get("releasedDate")

                if not title or not post_id:
                    continue

                # Must be a student programme, internship, fellowship, or apprentice role
                lower_title = title.lower()
                is_relevant = any(k in lower_title for k in [
                    "student", "intern", "fellow", "apprenti", "trainee"
                ])
                if not is_relevant:
                    continue

                job_url = f"https://jobs.smartrecruiters.com/CERN/{post_id}-{ref_num}" if ref_num else f"https://jobs.smartrecruiters.com/CERN/{post_id}"
                canonical_url = clean_canonical_url(job_url)
                company_name = normalize_company(self.company)

                date_tuple = self.parse_timestamp_to_ist(released_date)
                if date_tuple:
                    date_utc, date_ist, dt_ist = date_tuple
                    date_status = "confirmed"
                    evidence = f"SmartRecruiters verified release timestamp: {dt_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC: {date_utc})"
                else:
                    date_utc, date_ist = None, None
                    date_status = "unverified"
                    evidence = "No verified release timestamp provided"

                loc_info = post.get("location", {})
                city = loc_info.get("city", "Geneva")
                country = loc_info.get("country", "Switzerland")
                locations = [f"{city}, {country}"]
                work_mode = "Remote" if loc_info.get("remote") else "On-site"

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
                    "degrees_allowed": ["Bachelor's", "Master's"],
                    "sponsorship_status": "International research fellowship - CERN student visa sponsored",
                    "description_snippet": f"CERN Scientific Computing & Research position. Reference: {ref_num}. Location: {city}, {country}.",
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

            logger.info(f"Processed {len(results)} relevant positions from {self.company}.")
        except Exception as e:
            logger.error(f"Error in SmartRecruiters {self.company}: {e}", exc_info=True)
            raise

        return results

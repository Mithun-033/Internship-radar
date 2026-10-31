"""
Connector for NVIDIA Workday Careers API.
Fetches official direct career postings from NVIDIA's Workday ATS.
"""
from typing import List, Dict, Any
import logging
import datetime
import re
import requests

from .base import BaseConnector
from ..config import APP_TIMEZONE
from ..deduplication import clean_canonical_url, normalize_company, generate_listing_id
from ..eligibility import evaluate_eligibility
from ..matching import score_listing

logger = logging.getLogger("internship_radar.connectors.workday")

class WorkdayConnector(BaseConnector):
    def __init__(self, source_id: str, name: str, url: str, company: str = "NVIDIA", interval_minutes: int = 30):
        super().__init__(source_id, name, interval_minutes)
        self.url = url
        self.company = company
        self.base_job_url = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite"

    def fetch_listings(self) -> List[Dict[str, Any]]:
        results = []
        queries = ["intern", "gpu intern", "deep learning intern"]
        now_ist = datetime.datetime.now(APP_TIMEZONE)
        today_ist_str = now_ist.strftime("%Y-%m-%d")

        for query in queries:
            try:
                payload = {
                    "appliedFacets": {},
                    "limit": 20,
                    "offset": 0,
                    "searchText": query
                }
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                }
                resp = requests.post(self.url, json=payload, headers=headers, timeout=10)
                if resp.status_code != 200:
                    logger.warning(f"Workday {self.company} search '{query}' returned status {resp.status_code}")
                    continue

                data = resp.json()
                postings = data.get("jobPostings", [])
                logger.info(f"Workday {self.company} search '{query}' returned {len(postings)} postings.")

                for post in postings:
                    title = post.get("title", "").strip()
                    ext_path = post.get("externalPath", "").strip()
                    posted_on = post.get("postedOn", "").strip()
                    loc_text = post.get("locationsText", "")

                    if not title or not ext_path:
                        continue

                    # Must be an explicit internship or student role
                    if not any(k in title.lower() for k in ["intern", "co-op", "coop", "fellow", "apprentice", "trainee", "student"]):
                        continue

                    # Direct link to NVIDIA's official posting
                    full_url = f"{self.base_job_url}{ext_path}"
                    canonical_url = clean_canonical_url(full_url)
                    company_name = normalize_company(self.company)

                    # Determine posting date and evidence
                    date_posted_utc = None
                    date_posted_ist = None
                    date_status = "unverified"
                    evidence = f"NVIDIA Workday posted status: '{posted_on}'"

                    if "today" in posted_on.lower():
                        date_posted_ist = today_ist_str
                        date_posted_utc = now_ist.astimezone(datetime.timezone.utc).isoformat()
                        date_status = "confirmed"
                        evidence = f"NVIDIA Workday verified status: 'Posted Today' ({today_ist_str} IST)"
                    elif "yesterday" in posted_on.lower():
                        yesterday = now_ist - datetime.timedelta(days=1)
                        date_posted_ist = yesterday.strftime("%Y-%m-%d")
                        date_posted_utc = yesterday.astimezone(datetime.timezone.utc).isoformat()
                        date_status = "confirmed"
                        evidence = f"NVIDIA Workday verified status: 'Posted Yesterday' ({date_posted_ist} IST)"
                    else:
                        # Extract days ago if present: e.g. "Posted 5 Days Ago"
                        match = re.search(r'posted\s+(\d+)\s+days?\s+ago', posted_on.lower())
                        if match:
                            days_ago = int(match.group(1))
                            past_date = now_ist - datetime.timedelta(days=days_ago)
                            date_posted_ist = past_date.strftime("%Y-%m-%d")
                            date_posted_utc = past_date.astimezone(datetime.timezone.utc).isoformat()
                            date_status = "confirmed"
                            evidence = f"NVIDIA Workday verified status: 'Posted {days_ago} Days Ago' ({date_posted_ist} IST)"

                    locations = [loc_text] if loc_text else ["Global"]
                    work_mode = "Remote" if "remote" in loc_text.lower() else "On-site"

                    listing_id = generate_listing_id(company_name, title, canonical_url)

                    raw_listing = {
                        "id": listing_id,
                        "company": company_name,
                        "title": title,
                        "canonical_url": canonical_url,
                        "original_url": full_url,
                        "source_id": self.source_id,
                        "source_name": self.name,
                        "locations": locations,
                        "work_mode": work_mode,
                        "date_posted_utc": date_posted_utc,
                        "date_posted_ist": date_posted_ist,
                        "date_verification_status": date_status,
                        "date_source_evidence": evidence,
                        "degrees_allowed": ["Bachelor's"] if "phd" not in title.lower() else ["PhD"],
                        "sponsorship_status": "Varies by location",
                        "description_snippet": f"NVIDIA Career Posting. Location: {loc_text}. Posted: {posted_on}.",
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

                self.sleep_rate_limit()
            except Exception as e:
                logger.error(f"Error in Workday query '{query}': {e}")

        logger.info(f"Total Workday {self.company} listings fetched: {len(results)}")
        return results

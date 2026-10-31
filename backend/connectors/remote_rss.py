"""
Connector for Remote developer boards: RemoteOK and WeWorkRemotely RSS.
Discovers remote ML, AI, and backend opportunities accessible from anywhere.
"""
from typing import List, Dict, Any
import logging
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
import re
from bs4 import BeautifulSoup

from .base import BaseConnector
from ..deduplication import clean_canonical_url, normalize_company, generate_listing_id
from ..eligibility import evaluate_eligibility
from ..matching import score_listing

logger = logging.getLogger("internship_radar.connectors.remote_rss")

TARGET_KEYWORDS = [
    "intern", "internship", "student", "apprentice", "trainee", "fellow", "co-op", "coop", "working student"
]

class RemoteOKConnector(BaseConnector):
    def __init__(self, source_id: str, name: str, url: str = "https://remoteok.com/api", interval_minutes: int = 60):
        super().__init__(source_id, name, interval_minutes)
        self.url = url

    def fetch_listings(self) -> List[Dict[str, Any]]:
        results = []
        try:
            logger.info("Fetching RemoteOK jobs...")
            resp = self.session.get(self.url, timeout=12)
            if resp.status_code != 200:
                logger.error(f"RemoteOK fetch failed with status {resp.status_code}")
                return results

            items = resp.json()
            # First item in remoteok is legal disclosure
            jobs = items[1:] if len(items) > 1 and isinstance(items[0], dict) and "legal" in items[0] else items

            for job in jobs:
                title = job.get("position", "").strip()
                company_raw = job.get("company", "").strip()
                if not title or not company_raw:
                    continue

                lower_title = title.lower()
                tags = [str(t).lower() for t in job.get("tags", [])]
                all_text = f"{lower_title} {' '.join(tags)}"

                # Check relevance
                if not any(k in all_text for k in TARGET_KEYWORDS):
                    continue

                apply_url = job.get("url") or job.get("apply_url")
                if not apply_url:
                    continue

                canonical_url = clean_canonical_url(apply_url)
                company = normalize_company(company_raw)

                date_val = job.get("date")
                date_tuple = self.parse_timestamp_to_ist(date_val)
                if date_tuple:
                    date_utc, date_ist, dt_ist = date_tuple
                    date_status = "confirmed"
                    evidence = f"RemoteOK verified posting timestamp: {dt_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC: {date_utc})"
                else:
                    date_utc, date_ist = None, None
                    date_status = "unverified"
                    evidence = "No verified date timestamp in RemoteOK entry"

                desc_raw = job.get("description", "")
                snippet = ""
                if desc_raw:
                    clean_desc = BeautifulSoup(desc_raw, "html.parser").get_text(" ", strip=True)
                    snippet = clean_desc[:350] + "..." if len(clean_desc) > 350 else clean_desc

                locations = ["Remote / Worldwide"]
                listing_id = generate_listing_id(company, title, canonical_url)

                raw_listing = {
                    "id": listing_id,
                    "company": company,
                    "title": title,
                    "canonical_url": canonical_url,
                    "original_url": apply_url,
                    "source_id": self.source_id,
                    "source_name": self.name,
                    "locations": locations,
                    "work_mode": "Remote",
                    "date_posted_utc": date_utc,
                    "date_posted_ist": date_ist,
                    "date_verification_status": date_status,
                    "date_source_evidence": evidence,
                    "degrees_allowed": ["Bachelor's"],
                    "sponsorship_status": "Global Remote Opportunity",
                    "description_snippet": snippet or "Remote software / ML role.",
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

            logger.info(f"Processed {len(results)} relevant jobs from RemoteOK.")
        except Exception as e:
            logger.error(f"Error in RemoteOK connector: {e}", exc_info=True)
            raise

        return results


class WWRConnector(BaseConnector):
    def __init__(self, source_id: str, name: str, url: str, interval_minutes: int = 60):
        super().__init__(source_id, name, interval_minutes)
        self.url = url

    def fetch_listings(self) -> List[Dict[str, Any]]:
        results = []
        try:
            logger.info(f"Fetching RSS feed from {self.url}...")
            resp = self.session.get(self.url, timeout=12)
            if resp.status_code != 200:
                logger.error(f"RSS fetch failed for {self.url}: status {resp.status_code}")
                return results

            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            logger.info(f"Found {len(items)} items in RSS feed.")

            for it in items:
                raw_title = (it.find("title").text or "").strip()
                link = (it.find("link").text or "").strip()
                pub_date_str = (it.find("pubDate").text or "").strip()

                if not raw_title or not link:
                    continue

                # Title format is often: "Company: Job Title"
                if ":" in raw_title:
                    company_raw, title = raw_title.split(":", 1)
                else:
                    company_raw = "Remote Tech"
                    title = raw_title

                company = normalize_company(company_raw.strip())
                title = title.strip()

                # Filter strictly for internships, co-ops, apprenticeships, and student roles
                if not any(k in title.lower() for k in ["intern", "internship", "student", "apprentice", "trainee", "fellow", "co-op", "coop", "placement"]):
                    continue

                canonical_url = clean_canonical_url(link)

                # Parse RFC 2822 pubDate
                date_utc, date_ist, dt_ist = None, None, None
                date_status = "unverified"
                evidence = "No pubDate in RSS item"

                if pub_date_str:
                    try:
                        dt = parsedate_to_datetime(pub_date_str)
                        date_tuple = self.parse_timestamp_to_ist(dt.isoformat())
                        if date_tuple:
                            date_utc, date_ist, dt_ist = date_tuple
                            date_status = "confirmed"
                            evidence = f"WeWorkRemotely RSS verified publication timestamp: {dt_ist.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC: {date_utc})"
                    except Exception as e:
                        logger.debug(f"Failed parsing RSS pubDate {pub_date_str}: {e}")

                desc_elem = it.find("description")
                snippet = ""
                if desc_elem is not None and desc_elem.text:
                    clean_desc = BeautifulSoup(desc_elem.text, "html.parser").get_text(" ", strip=True)
                    snippet = clean_desc[:350] + "..." if len(clean_desc) > 350 else clean_desc

                listing_id = generate_listing_id(company, title, canonical_url)

                raw_listing = {
                    "id": listing_id,
                    "company": company,
                    "title": title,
                    "canonical_url": canonical_url,
                    "original_url": link,
                    "source_id": self.source_id,
                    "source_name": self.name,
                    "locations": ["Remote"],
                    "work_mode": "Remote",
                    "date_posted_utc": date_utc,
                    "date_posted_ist": date_ist,
                    "date_verification_status": date_status,
                    "date_source_evidence": evidence,
                    "degrees_allowed": ["Bachelor's"],
                    "sponsorship_status": "Remote Opportunity",
                    "description_snippet": snippet or f"Remote role at {company}.",
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

            logger.info(f"Processed {len(results)} listings from RSS feed.")
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}", exc_info=True)
            raise

        return results

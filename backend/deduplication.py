"""
Deduplication and URL normalization module.
Standardizes company names, titles, and strips tracking parameters to avoid duplicates.
"""
import re
import urllib.parse
import hashlib
from typing import Tuple

COMPANY_ALIASES = {
    "nvidia corporation": "NVIDIA",
    "nvidia inc": "NVIDIA",
    "nvidia": "NVIDIA",
    "meta platforms": "Meta",
    "facebook": "Meta",
    "meta": "Meta",
    "google llc": "Google",
    "google inc": "Google",
    "google": "Google",
    "apple inc.": "Apple",
    "apple inc": "Apple",
    "apple": "Apple",
    "microsoft corporation": "Microsoft",
    "microsoft": "Microsoft",
    "amazon web services": "Amazon",
    "amazon.com": "Amazon",
    "amazon": "Amazon",
    "anthropic pbc": "Anthropic",
    "anthropic": "Anthropic",
    "scale ai, inc.": "Scale AI",
    "scale ai": "Scale AI",
    "scaleai": "Scale AI",
    "perplexity ai": "Perplexity",
    "perplexity": "Perplexity",
    "databricks inc": "Databricks",
    "databricks": "Databricks",
    "cloudflare, inc.": "Cloudflare",
    "cloudflare": "Cloudflare",
    "cern openlab": "CERN",
    "cern": "CERN"
}

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "source", "gh_src", "lever-origin", "lever-source", "mode",
    "sessionid", "referral", "fbclid", "gclid", "trk", "trackingid", "ats"
}

def normalize_company(company: str) -> str:
    """Normalizes company name using canonical aliases or clean casing."""
    if not company:
        return "Unknown Company"
    clean = re.sub(r'[\(\)\[\],]', '', company).strip().lower()
    if clean in COMPANY_ALIASES:
        return COMPANY_ALIASES[clean]
    # Check prefixes
    for k, v in COMPANY_ALIASES.items():
        if clean.startswith(k):
            return v
    # Capitalize words
    return " ".join([w.capitalize() for w in company.strip().split()])

def clean_canonical_url(url: str) -> str:
    """Strips tracking query parameters and standardizes URL structure."""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        query_dict = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)
        # Filter out tracking parameters
        filtered_query = {k: v for k, v in query_dict.items() if k.lower() not in TRACKING_PARAMS}
        new_query = urllib.parse.urlencode(filtered_query, doseq=True)
        # Standardize path
        clean_path = parsed.path.rstrip('/')
        if not clean_path:
            clean_path = "/"
        clean_url = urllib.parse.urlunparse((
            parsed.scheme.lower() or "https",
            parsed.netloc.lower(),
            clean_path,
            parsed.params,
            new_query,
            "" # omit fragments
        ))
        return clean_url
    except Exception:
        return url.strip()

def normalize_title(title: str) -> str:
    """Normalizes job titles by removing noisy suffixes, punctuation, and lowercasing."""
    if not title:
        return ""
    t = title.lower().strip()
    # Remove seasonal tags in parentheses/brackets e.g. (Summer 2027), [Winter 2026]
    t = re.sub(r'[\(\[\{].*?[\)\]\}]', '', t)
    # Remove specific terms
    t = re.sub(r'\b(summer|fall|winter|spring|internship|intern|2025|2026|2027|2028|2029)\b', '', t)
    # Strip symbols
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    return " ".join(t.split())

def generate_listing_id(company: str, title: str, canonical_url: str) -> str:
    """Generates a stable, deterministic unique ID for deduplication."""
    norm_comp = normalize_company(company).lower()
    norm_tit = normalize_title(title)
    clean_u = clean_canonical_url(canonical_url).lower()

    # If canonical URL has a distinct job path, use company + url hash
    key = f"{norm_comp}|{norm_tit}|{clean_u}"
    return hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]

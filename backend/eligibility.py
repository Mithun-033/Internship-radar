"""
Eligibility evaluation module.
Strictly checks undergraduate status, graduation year 2029 compatibility,
degree requirements, citizenship/visa constraints, and location criteria.

ABSOLUTE REQUIREMENT: Complete disqualification of ANY PhD, Master's, MS-only,
doctoral, or graduate degree positions for undergraduate eligibility.
"""
import re
import json
from typing import Dict, Any, List, Tuple

INDIA_CITIES = [
    "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "delhi", "noida", 
    "gurgaon", "gurugram", "chennai", "trivandrum", "thiruvananthapuram", 
    "kochi", "cochin", "kolkata", "ahmedabad", "india"
]

def is_india_location(loc_str: str) -> bool:
    """
    Returns True if location is in India.
    Crucially excludes 'Indiana' and 'Indianapolis' (USA) false-positives.
    """
    if not loc_str:
        return False
    l = str(loc_str).lower()
    if "indiana" in l or "indianapolis" in l:
        return False
    if "india" in l:
        return True
    return any(city in l for city in INDIA_CITIES)

DISQUALIFYING_ROLES = [
    r'\bdirector\b', r'\bmanager\b', r'\bprincipal\b', r'\bsenior\b', 
    r'\bhead of\b', r'\bvice president\b', r'\bvp\b', r'\blead engineer\b',
    r'\bstaff engineer\b', r'\bstaff\b', r'\bpostdoc\b', r'\bpostdoctoral\b', r'\bfaculty\b'
]

# Strict Disqualifiers: ANY match here will cause IMMEDIATE exclusion
GRADUATE_ONLY_PATTERNS = [
    r'\bph\.?d\b',
    r'\bdoctoral\b',
    r'\bdoctorate\b',
    r'\bpostdoc\b',
    r'\bpostdoctoral\b',
    r'\bmaster\'?s\b',
    r'\bmasters\b',
    r'\bm\.s\b',
    r'\bms\s+intern\b',
    r'\bms/phd\b',
    r'\bphd/ms\b',
    r'\bms\s+or\s+phd\b',
    r'\bphd\s+or\s+ms\b',
    r'\bmba\b',
    r'\bgraduate\s+intern(?:ship)?\b',
    r'\bgrad\s+intern(?:ship)?\b',
    r'\bgraduate\s+student\b',
    r'\badvanced\s+degree\b',
    r'\bassociate\s+intern(?:ship)?\b',
    r'\bsummer\s+associate\b',
    r'\bmaster[^\w\s]?s?\s+intern(?:ship)?\b',
    r'\bstudent\s+researcher\b',
    r'\bgraduate\s+research\b',
    r'\bgraduate\s+assistant\b',
    r'\bpost-graduate\b',
    r'\bpostgraduate\b',
    r'\bpg\s+intern\b',
    r'\bm1\b',
    r'\bm2\b',
    r'\bm1/m2\b',
    r'\bcompleted\s+(?:bachelor\'?s|bs|b\.?tech)\b'
]

US_AUTH_ONLY_PATTERNS = [
    r'\bus\s+citizenship\s+required\b',
    r'\bmust\s+be\s+a\s+u\.?s\.?\s+citizen\b',
    r'\bsecurity\s+clearance\s+required\b',
    r'\bactive\s+secret\s+clearance\b',
    r'\bno\s+(?:visa\s+)?sponsorship\s+(?:is\s+)?available\b',
    r'\bwithout\s+(?:the\s+need\s+for\s+)?sponsorship\b',
    r'\bnot\s+eligible\s+for\s+(?:visa\s+)?sponsorship\b',
    r'\bdo\s+not\s+offer\s+visa\s+sponsorship\b',
    r'\bitar\s+compliance\b',
    r'\bmust\s+hold\s+us\s+work\s+authorization\b'
]

PAST_GRAD_PATTERNS = [
    r'\bgraduat(?:ing|ion)\s+(?:in|by)\s+(?:2024|2025|december\s+2025)\b',
    r'\bclass\s+of\s+2025\b',
    r'\bclass\s+of\s+2026\s+only\b'
]

UNDERGRAD_FRIENDLY_PATTERNS = [
    r'\bbachelor\'?s\b', r'\bb\.?tech\b', r'\bundergraduate\b', r'\bbs\b',
    r'\bsophomore\b', r'\bjunior\b', r'\bsecond-year\b', r'\bthird-year\b',
    r'\bstudent\b', r'\bcollege\b', r'\buniversity\b'
]

INTERNSHIP_POSITIVE_PATTERNS = [
    r'\bintern(?:ship|ships|s)?\b',
    r'\bntern\b', # Common scraping typo, e.g. "ntern, Engineer Software"
    r'\bco-?op(?:erative|s)?\b',
    r'\bcoop(?:s)?\b',
    r'\bfellow(?:ship|ships|s)?\b',
    r'\btrainee(?:ship|ships|s)?\b',
    r'\bapprentice(?:ship|ships|s)?\b',
    r'\bapprentissage\b',
    r'\bstudent(?:s)?\b',
    r'\bplacement(?:s)?\b',
    r'\bwerkstudent\b',
    r'\bworking\s+student\b',
    r'\bpart-time\s+student\b',
    r'\bpracticum\b',
    r'\bstagi(?:aire|ere)s?\b',
    r'\bresiden(?:t|cy)\b',
    r'\bscholar(?:ship|s)?\b',
    r'\bsummer\s+(?:analyst|associate|researcher|developer|engineer|scholar|program)\b',
    r'\bundergrad(?:uate)?\b'
]

def is_internship_or_student_role(title: str, desc: str = "") -> bool:
    """
    Returns True if the role is definitively an undergraduate internship, co-op,
    fellowship, student placement, traineeship, or apprenticeship.
    Strictly returns False for permanent full-time jobs, experienced positions, and non-student roles.
    """
    t_clean = (title or "").lower().strip()

    # Hard rejection for explicit full-time or permanent indicators in title
    if re.search(r'\bfull-?time\b', t_clean) and not any(k in t_clean for k in ['intern', 'co-op', 'coop', 'student', 'fellow']):
        return False
    if re.search(r'\bpermanent\b', t_clean):
        return False
    if re.search(r'\bdirect\s+hire\b', t_clean):
        return False

    # Check title for positive internship patterns
    for pat in INTERNSHIP_POSITIVE_PATTERNS:
        if re.search(pat, t_clean):
            return True

    return False

def parse_degrees_list(degrees_raw: Any) -> List[str]:
    """Parses degree metadata from json string, list, or comma-separated string."""
    if not degrees_raw:
        return []
    if isinstance(degrees_raw, list):
        return [str(d).strip() for d in degrees_raw if str(d).strip()]
    if isinstance(degrees_raw, str):
        try:
            parsed = json.loads(degrees_raw)
            if isinstance(parsed, list):
                return [str(d).strip() for d in parsed if str(d).strip()]
        except Exception:
            pass
        return [d.strip() for d in degrees_raw.split(",") if d.strip()]
    return []

def is_graduate_or_phd_role(title: str, desc: str = "", degrees: Any = None) -> bool:
    """
    Returns True if the listing is targeting PhD, Master's, MBA, or Postdoctoral candidates.
    Such roles are strictly non-undergraduate and must be completely excluded.
    """
    t_clean = (title or "").lower()
    d_clean = (desc or "").lower()

    # 1. Check title first (highest precision)
    for pat in GRADUATE_ONLY_PATTERNS:
        if re.search(pat, t_clean):
            # Special case: 'master data' in enterprise systems (ERP/SAP) is not a Master's degree
            if "master data" in t_clean and not re.search(r'master\'?s', t_clean):
                continue
            return True

    # 2. Check degrees metadata (e.g. from ATS or aggregator)
    deg_list = parse_degrees_list(degrees)
    if deg_list:
        deg_str = " ".join(d.lower() for d in deg_list)
        has_undergrad = any(u in deg_str for u in ["bachelor", "b.tech", "undergrad", "bs", "ba", "associate"])
        # If degrees are specified and undergraduate is NOT among them, it is strictly graduate!
        if not has_undergrad:
            return True

    # 3. Check description for explicit enrollment prerequisites
    for pat in [
        r'\bmust be (?:enrolled|pursuing) a (?:ph\.?d|master)', 
        r'\bcurrently pursuing (?:a )?(?:ph\.?d|master)', 
        r'\bph\.?d\.? (?:student|candidate|degree) required',
        r'\bmaster\'?s (?:student|candidate|degree) required',
        r'\benrolled in a master\'?s or ph\.?d',
        r'\benrolled in a ph\.?d or master\'?s',
        r'\bpursuing a master\'?s degree',
        r'\bpursuing a ph\.?d degree'
    ]:
        if re.search(pat, d_clean):
            return True

    # 4. Check for full-time Senior/Staff roles that accidentally lack 'intern'
    if not any(k in t_clean for k in ['intern', 'student', 'fellow', 'co-op', 'apprentice']):
        for pat in [r'\bsenior\b', r'\bstaff\b', r'\bprincipal\b', r'\bdirector\b', r'\bhead of\b', r'\bvp\b', r'\blead engineer\b']:
            if re.search(pat, t_clean):
                return True

    return False

def evaluate_eligibility(listing: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Evaluates whether the candidate is eligible for a given position.
    Returns:
        status: "eligible" | "potentially_eligible" | "ineligible"
        reasons: List of explanatory justification strings
    """
    title = (listing.get("title") or "").strip()
    desc = (listing.get("description_snippet") or "").strip()
    locations = [str(loc).lower() for loc in listing.get("locations", [])]
    sponsorship = (listing.get("sponsorship_status") or "").lower()
    degrees = listing.get("degrees_allowed", [])
    
    full_text = f"{title.lower()} {desc.lower()} {' '.join(locations)} {sponsorship}"
    reasons = []

    # 0. HARD REQUIREMENT: Position MUST be an undergraduate internship or student placement
    if not is_internship_or_student_role(title, desc):
        reasons.append("Excluded: Regular full-time job or experienced position, not an undergraduate internship or student placement.")
        return "ineligible", reasons

    # 1. HARD BLOCK: PhD / Master's / Graduate / Senior roles
    if is_graduate_or_phd_role(title, desc, degrees):
        reasons.append("Excluded: Requires Master's, PhD, graduate enrollment, or is a senior non-intern role. Candidate is an undergraduate student.")
        return "ineligible", reasons

    # 2. Check for senior/full-time false positives
    for pat in DISQUALIFYING_ROLES:
        if re.search(pat, title.lower()) and not any(k in title.lower() for k in ['intern', 'fellow', 'student', 'apprentice', 'co-op']):
            reasons.append("Excluded: Appears to be a permanent/senior role, not an undergraduate internship.")
            return "ineligible", reasons

    # 3. Check for incompatible graduation years
    for pat in PAST_GRAD_PATTERNS:
        if re.search(pat, desc.lower()):
            reasons.append("Excluded: Graduation year requirements (2025/early 2026) are incompatible with candidate's 2029 graduation date.")
            return "ineligible", reasons

    # 4. Check for strict US Citizenship / No Sponsorship constraints
    for pat in US_AUTH_ONLY_PATTERNS:
        if re.search(pat, full_text):
            reasons.append("Excluded: Requires US citizenship, active clearance, or explicitly denies visa sponsorship.")
            return "ineligible", reasons

    if "no sponsorship" in sponsorship or "will not sponsor" in sponsorship:
        reasons.append("Excluded: Source metadata specifies no visa sponsorship is offered.")
        return "ineligible", reasons

    # 5. Location and Work Authorization evaluation
    is_india = any(is_india_location(loc) for loc in locations)
    is_remote = listing.get("work_mode", "").lower() == "remote" or any("remote" in loc for loc in locations)
    
    deg_list = parse_degrees_list(degrees)
    is_explicit_undergrad = (
        any("bachelor" in d.lower() or "b.tech" in d.lower() for d in deg_list) or 
        any(re.search(pat, full_text) for pat in UNDERGRAD_FRIENDLY_PATTERNS)
    )

    if is_india:
        reasons.append("Eligible: Role located in India; fully eligible for Indian citizens without visa hurdles.")
        if is_explicit_undergrad:
            reasons.append("Eligible: Undergraduate (B.Tech) degree enrollment is supported.")
        return "eligible", reasons

    if is_remote and ("worldwide" in full_text or "global" in full_text or "anywhere" in full_text or is_india):
        reasons.append("Eligible: Worldwide/Global Remote work arrangement accessible from India.")
        return "eligible", reasons

    # International locations (US, UK, Europe, Canada, etc.)
    company_name = (listing.get("company") or "").lower()
    is_top_sponsor = any(c in company_name for c in ["cern", "google", "nvidia", "microsoft", "apple", "meta", "anthropic", "openai", "perplexity", "scale ai"])

    if is_top_sponsor or "j-1" in full_text or "sponsors" in full_text or "intern" in title.lower():
        if is_remote:
            reasons.append("Potentially eligible: Remote role based abroad; requires verifying international remote contracting from India.")
            return "potentially_eligible", reasons
        else:
            reasons.append("Potentially eligible: International on-site internship. J-1 or student visa sponsorship required for Indian students.")
            return "potentially_eligible", reasons

    reasons.append("Potentially eligible: Undergraduate eligibility and international work authorization must be verified on official application.")
    return "potentially_eligible", reasons

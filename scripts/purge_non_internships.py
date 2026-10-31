import sys, json
sys.path.insert(0, '.')
from backend.database import get_connection
from backend.eligibility import is_internship_or_student_role, evaluate_eligibility

def purge_non_internships():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, company, title, description_snippet, degrees_allowed, locations, sponsorship_status FROM listings WHERE is_active=1")
    rows = c.fetchall()
    
    purged_count = 0
    purged_samples = []

    for r in rows:
        lid, comp, title, desc, degs_raw, locs_raw, spons = r
        try:
            degs = json.loads(degs_raw) if degs_raw else []
        except:
            degs = []
        try:
            locs = json.loads(locs_raw) if locs_raw else []
        except:
            locs = []

        listing = {
            "title": title,
            "description_snippet": desc,
            "degrees_allowed": degs,
            "locations": locs,
            "sponsorship_status": spons
        }

        status, reasons = evaluate_eligibility(listing)
        if status == "ineligible":
            purged_count += 1
            if len(purged_samples) < 20:
                purged_samples.append((comp, title, reasons[0]))
            reasons_json = json.dumps(reasons)
            c.execute("""
                UPDATE listings 
                SET is_active = 0, eligibility_status = 'ineligible', eligibility_reasons = ?
                WHERE id = ?
            """, (reasons_json, lid))

    conn.commit()
    conn.close()
    print(f"Purged and deactivated {purged_count} non-internship / ineligible roles.")
    print("Samples of purged roles:")
    for comp, tit, r in purged_samples:
        s = f" - [{comp}] {tit} -> {r}"
        print(s.encode('ascii', 'replace').decode())

if __name__ == "__main__":
    purge_non_internships()

"""
Database Purge Script: Removes/Deactivates PhD, Master's, and Senior non-intern listings.
Ensures the dashboard presents exclusively undergraduate-eligible opportunities.
"""
import sqlite3
import json
import re

from backend.eligibility import is_graduate_or_phd_role

def purge_database():
    conn = sqlite3.connect("data/internships.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, company, title, degrees_allowed, description_snippet, eligibility_reasons
        FROM listings
        WHERE is_active = 1
    """)
    rows = cursor.fetchall()
    print(f"Total active listings before purge: {len(rows)}")

    purged_count = 0
    reasons_json = json.dumps(["Excluded: Strictly non-undergraduate (requires Master's, PhD, MBA, or is senior role)."])
    for r in rows:
        lid, company, title, degs_json, snippet, reasons_json_db = r
        if is_graduate_or_phd_role(title, snippet, degs_json):
            cursor.execute("""
                UPDATE listings 
                SET is_active = 0, eligibility_status = 'ineligible',
                    eligibility_reasons = ?
                WHERE id = ?
            """, (reasons_json, lid))
            purged_count += 1
            print(f" - Purged: [{company}] {title}")

    conn.commit()
    conn.close()
    print(f"\nPurge complete: {purged_count} graduate/senior listings deactivated.")

if __name__ == "__main__":
    purge_database()

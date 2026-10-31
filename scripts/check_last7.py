import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "data" / "internships.db"
conn = sqlite3.connect(str(db_path))
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM listings WHERE date_posted_ist >= date('2026-10-22', '-7 days') AND is_active = 1;")
total_7d = c.fetchone()[0]
print("Total last 7 days:", total_7d)

c.execute("SELECT company, title, date_posted_ist, match_category, match_score FROM listings WHERE date_posted_ist >= date('2026-10-22', '-7 days') AND is_active = 1 ORDER BY match_score DESC LIMIT 5;")
for r in c.fetchall():
    print(r)

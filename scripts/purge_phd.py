"""
Purge script to remove test fixtures, PhD/Master's internships, and recalculate statistics.
"""
import sqlite3
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.eligibility import is_graduate_or_phd_role

DB_PATH = BASE_DIR / "data" / "internships.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Delete synthetic fixtures
cursor.execute("DELETE FROM listings WHERE id LIKE 'test_%' OR canonical_url LIKE '%/test';")
deleted_test = cursor.rowcount

# 2. Find and delete PhD / Master's / Doctoral positions
cursor.execute("SELECT id, title, description_snippet, degrees_allowed FROM listings;")
rows = cursor.fetchall()

to_delete = []
for r in rows:
    degs = []
    if r["degrees_allowed"]:
        try:
            degs = json.loads(r["degrees_allowed"])
        except:
            degs = []
    if is_graduate_or_phd_role(r["title"], r["description_snippet"], degs):
        to_delete.append(r["id"])

for lid in to_delete:
    cursor.execute("DELETE FROM listings WHERE id = ?;", (lid,))

conn.commit()
print(f"[PURGE COMPLETE] Deleted {deleted_test} test items and {len(to_delete)} PhD/Master's roles.")

cursor.execute("SELECT COUNT(*) FROM listings;")
print("Remaining genuine undergraduate listings:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM listings WHERE is_today_ist = 1;")
print("Remaining confirmed Today IST undergraduate listings:", cursor.fetchone()[0])

conn.close()

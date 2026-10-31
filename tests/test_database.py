"""
Tests for SQLite Database Persistence, Audit Trail, and State Tracking.
"""
import pytest
import os
import tempfile
import backend.database as db_mod
from backend.database import init_db, get_connection, upsert_listing, get_stats, update_daily_flags

@pytest.fixture(autouse=True)
def use_test_db(monkeypatch):
    """Ensures tests run in a separate temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name
    monkeypatch.setattr(db_mod, "DB_PATH", test_db_path)
    init_db()
    yield test_db_path
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except:
            pass

def test_database_init_and_sources_population():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sources;")
    count = cursor.fetchone()[0]
    assert count >= 10
    conn.close()

def test_upsert_and_retrieve_listing():
    test_item = {
        "id": "test_nvidia_gpu_001",
        "company": "NVIDIA",
        "title": "GPU Kernel Engineering Intern - Summer 2027",
        "canonical_url": "https://nvidia.wd5.myworkdayjobs.com/test",
        "original_url": "https://nvidia.wd5.myworkdayjobs.com/test",
        "source_id": "nvidia_careers",
        "source_name": "NVIDIA Career Site",
        "locations": ["Bengaluru, India"],
        "work_mode": "On-site",
        "date_posted_utc": "2026-10-22T04:00:00Z",
        "date_posted_ist": "2026-10-22",
        "is_today_ist": 1,
        "date_verification_status": "confirmed",
        "date_source_evidence": "NVIDIA Workday verified status: Posted Today",
        "first_seen_at": "2026-10-22T04:00:00Z",
        "last_seen_at": "2026-10-22T04:00:00Z",
        "degrees_allowed": ["Bachelor's"],
        "sponsorship_status": "Eligible India",
        "eligibility_status": "eligible",
        "eligibility_reasons": ["Eligible: Domestic India location."],
        "match_score": 96,
        "match_category": "GPU & Triton Optimization",
        "match_reasons": ["Top Priority Match for Triton and CUDA kernels."],
        "matched_skills": ["Triton", "CUDA", "PyTorch"],
        "matched_projects": ["Triton MuonAdamW"],
        "missing_skills": [],
        "description_snippet": "Implement custom Triton kernels for accelerated LLM training.",
        "user_saved": 0,
        "user_status": "none"
    }

    is_new = upsert_listing(test_item)
    assert is_new is True

    # Retrieve from DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM listings WHERE id = ?", ("test_nvidia_gpu_001",))
    row = cursor.fetchone()
    assert row is not None
    assert row["company"] == "NVIDIA"
    assert row["match_score"] == 96
    assert row["is_today_ist"] == 1
    conn.close()

    # Test stats
    stats = get_stats("2026-10-22")
    assert stats["today_new_count"] >= 1
    assert stats["strong_matches_count"] >= 1

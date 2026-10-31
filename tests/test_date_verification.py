"""
Tests for Date Verification and Asia/Kolkata Timezone Handling.
"""
import pytest
import datetime
import zoneinfo
from backend.connectors.base import BaseConnector
from backend.config import APP_TIMEZONE

class DummyConnector(BaseConnector):
    def fetch_listings(self):
        return []

def test_parse_timestamp_iso_utc():
    conn = DummyConnector("dummy", "Dummy")
    # 2026-10-22T01:30:00Z -> In Asia/Kolkata (+05:30) is 2026-10-22 07:00:00
    res = conn.parse_timestamp_to_ist("2026-10-22T01:30:00Z")
    assert res is not None
    iso_utc, date_ist, dt_ist = res
    assert date_ist == "2026-10-22"
    assert dt_ist.tzinfo == APP_TIMEZONE

def test_parse_timestamp_timezone_shift():
    conn = DummyConnector("dummy", "Dummy")
    # 2026-10-21T21:00:00Z -> In Asia/Kolkata (+05:30) is 2026-10-22 02:30:00 AM IST!
    res = conn.parse_timestamp_to_ist("2026-10-21T21:00:00Z")
    assert res is not None
    iso_utc, date_ist, dt_ist = res
    assert date_ist == "2026-10-22"

def test_parse_older_date_excluded_from_today():
    conn = DummyConnector("dummy", "Dummy")
    # 2026-10-20T10:00:00Z -> 2026-10-20 IST
    res = conn.parse_timestamp_to_ist("2026-10-20T10:00:00Z")
    assert res is not None
    iso_utc, date_ist, dt_ist = res
    assert date_ist == "2026-10-20"
    assert date_ist != "2026-10-22"

def test_parse_unix_timestamp():
    conn = DummyConnector("dummy", "Dummy")
    # Unix timestamp for 2026-10-22 06:09:28 UTC: 1792649368
    ts = 1792649368
    res = conn.parse_timestamp_to_ist(ts)
    assert res is not None
    iso_utc, date_ist, dt_ist = res
    assert date_ist == "2026-10-22"

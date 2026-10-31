"""
Tests for Deduplication, Normalization, and Canonical URL cleaning.
"""
import pytest
from backend.deduplication import normalize_company, clean_canonical_url, normalize_title, generate_listing_id

def test_normalize_company():
    assert normalize_company("NVIDIA Corporation") == "NVIDIA"
    assert normalize_company("nvidia inc") == "NVIDIA"
    assert normalize_company("Anthropic PBC") == "Anthropic"
    assert normalize_company("Scale AI, Inc.") == "Scale AI"
    assert normalize_company("Perplexity AI") == "Perplexity"
    assert normalize_company("Google LLC") == "Google"

def test_clean_canonical_url_strips_tracking():
    raw_url = "https://boards.greenhouse.io/anthropic/jobs/12345?utm_source=linkedin&utm_campaign=fall&ref=indeed&gh_src=abc"
    clean = clean_canonical_url(raw_url)
    assert "utm_source" not in clean
    assert "ref" not in clean
    assert "gh_src" not in clean
    assert clean == "https://boards.greenhouse.io/anthropic/jobs/12345"

def test_deterministic_listing_id_deduplication():
    url1 = "https://jobs.ashbyhq.com/perplexity/123?utm_source=aggregator"
    url2 = "https://jobs.ashbyhq.com/perplexity/123?ref=test&sessionid=xyz"

    id1 = generate_listing_id("Perplexity AI", "Machine Learning Intern (Summer 2027)", url1)
    id2 = generate_listing_id("Perplexity", "Machine Learning Intern", url2)

    assert id1 == id2

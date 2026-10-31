"""
Tests for Strict Undergraduate Eligibility and Graduation Year Constraints.
"""
import pytest
from backend.eligibility import evaluate_eligibility

def test_reject_phd_only_roles():
    listing = {
        "title": "Applied Deep Learning PhD Research Intern - Fall 2026",
        "description_snippet": "Must be currently enrolled in a PhD program in Computer Science.",
        "degrees_allowed": ["PhD"],
        "locations": ["Santa Clara, CA"]
    }
    status, reasons = evaluate_eligibility(listing)
    assert status == "ineligible"
    assert any("undergraduate" in r.lower() or "phd" in r.lower() for r in reasons)

def test_reject_masters_and_doctoral_roles():
    for title in ["Machine Learning Master's Intern", "Doctoral Research Fellow", "MS/PhD Software Engineering Intern", "Postdoctoral Researcher"]:
        status, reasons = evaluate_eligibility({"title": title, "degrees_allowed": []})
        assert status == "ineligible"

def test_reject_incompatible_grad_year():
    listing = {
        "title": "Software Engineering Intern",
        "description_snippet": "Must be graduating by December 2025. Class of 2025 only.",
        "degrees_allowed": ["Bachelor's"],
        "locations": ["Bengaluru, India"]
    }
    status, reasons = evaluate_eligibility(listing)
    assert status == "ineligible"
    assert any("incompatible" in r.lower() for r in reasons)

def test_reject_us_citizenship_only():
    listing = {
        "title": "Defense Systems Software Intern",
        "description_snippet": "Active Secret clearance required. Must be a US Citizen.",
        "degrees_allowed": ["Bachelor's"],
        "locations": ["Salt Lake City, UT"],
        "sponsorship_status": "No sponsorship available"
    }
    status, reasons = evaluate_eligibility(listing)
    assert status == "ineligible"
    assert any("US citizenship" in r or "sponsorship" in r.lower() for r in reasons)

def test_accept_undergraduate_india():
    listing = {
        "title": "Systems Software Engineering Intern - Summer 2027",
        "description_snippet": "Open to Bachelor's and B.Tech students in Computer Science.",
        "degrees_allowed": ["Bachelor's"],
        "locations": ["Bengaluru, Karnataka, India"]
    }
    status, reasons = evaluate_eligibility(listing)
    assert status == "eligible"
    assert any("India" in r for r in reasons)

def test_accept_worldwide_remote():
    listing = {
        "title": "Machine Learning Intern",
        "description_snippet": "Worldwide remote role. Open to undergraduate students.",
        "degrees_allowed": ["Bachelor's"],
        "locations": ["Remote / Worldwide"],
        "work_mode": "Remote"
    }
    status, reasons = evaluate_eligibility(listing)
    assert status == "eligible"
    assert any("Remote" in r for r in reasons)

def test_international_on_site_labeled_potentially_eligible():
    listing = {
        "title": "Software Engineer Intern - Systems",
        "company": "Apple",
        "description_snippet": "London office. Undergraduate student pursuing degree in Computer Science.",
        "degrees_allowed": ["Bachelor's"],
        "locations": ["London, UK"],
        "work_mode": "On-site"
    }
    status, reasons = evaluate_eligibility(listing)
    assert status == "potentially_eligible"
    assert any("visa" in r.lower() or "sponsorship" in r.lower() for r in reasons)

def test_reject_full_time_actual_jobs():
    non_intern_roles = [
        "Software Engineer",
        "ML Engineer",
        "Product Manager",
        "Infrastructure SRE - HPC",
        "Platform Engineer - AI Infrastructure",
        "Quantitative Trader",
        "Full-Stack Web Developer",
        "Analog/Mixed-Signal Serdes Design Engineer",
        "Solutions Architect",
        "Risk Analyst"
    ]
    for title in non_intern_roles:
        listing = {
            "title": title,
            "company": "Tech Corp",
            "locations": ["Bengaluru, Karnataka, India"],
            "description_snippet": "Full-time engineering role with 3+ years experience.",
            "degrees_allowed": ["Bachelor's"]
        }
        status, reasons = evaluate_eligibility(listing)
        assert status == "ineligible", f"Expected {title} to be ineligible, got {status}"
        assert any("full-time" in r.lower() or "internship" in r.lower() for r in reasons)

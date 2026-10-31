"""
Tests for Resume-Based Relevance Scoring and Priority Ordering.
Checks that rankings follow technical candidate profile specialization:
GPU/Triton > LLM Research > ML Systems > Applied ML > Backend SWE.
"""
import pytest
from backend.matching import score_listing

def test_gpu_triton_highest_tier():
    listing = {
        "title": "Compiler and GPU Kernel Optimization Intern",
        "company": "NVIDIA",
        "description_snippet": "Implement custom Triton and CUDA kernels, operator fusion, and accelerated computing for deep learning."
    }
    score, category, reasons, matched_skills, matched_proj, missing_skills = score_listing(listing)
    assert category == "GPU & Triton Optimization"
    assert score >= 90
    assert any("Triton" in p for p in matched_proj)
    assert "Triton" in matched_skills or "CUDA" in matched_skills or "GPU Kernels" in matched_skills

def test_llm_research_second_tier():
    listing = {
        "title": "LLM Research Intern - Language Modeling",
        "company": "Anthropic",
        "description_snippet": "Research on decoder-only transformers, scaling laws, pretraining, RoPE, and GQA attention mechanisms in PyTorch."
    }
    score, category, reasons, matched_skills, matched_proj, missing_skills = score_listing(listing)
    assert category == "LLM Research & Modeling"
    assert score >= 85
    assert any("PocketGPT" in p for p in matched_proj)

def test_ml_systems_tier():
    listing = {
        "title": "ML Systems & Training Infrastructure Intern",
        "company": "Scale AI",
        "description_snippet": "Build distributed training infrastructure, PyTorch Lightning pipelines, and efficient inference engines."
    }
    score, category, reasons, matched_skills, matched_proj, missing_skills = score_listing(listing)
    assert category == "ML Systems & Training Infra"
    assert score >= 80

def test_applied_ml_tier():
    listing = {
        "title": "Computer Vision & Applied Deep Learning Intern",
        "company": "Roblox",
        "description_snippet": "Develop image classification models with PyTorch and automated hyperparameter optimization using Optuna."
    }
    score, category, reasons, matched_skills, matched_proj, missing_skills = score_listing(listing)
    assert category == "Applied AI / ML"
    assert 70 <= score <= 85
    assert any("FREUID" in p for p in matched_proj)

def test_backend_tier():
    listing = {
        "title": "Backend Software Engineering Intern",
        "company": "Stripe",
        "description_snippet": "Design high-performance REST APIs using FastAPI, Docker, and SQL databases."
    }
    score, category, reasons, matched_skills, matched_proj, missing_skills = score_listing(listing)
    assert category == "Backend & Systems"
    assert 60 <= score <= 78

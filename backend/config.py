"""
Configuration for Internship Radar.
Defines timezone, candidate profile, paths, collection intervals, and source registry.
"""
from pathlib import Path
import os
import zoneinfo

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = str(DATA_DIR / "internships.db")
CONFIG_FILE = str(BASE_DIR / "config.json")

# Timezone requirement: Asia/Kolkata
APP_TIMEZONE = zoneinfo.ZoneInfo("Asia/Kolkata")
TIMEZONE_STR = "Asia/Kolkata"

# Server configuration
HOST = os.getenv("RADAR_HOST", "127.0.0.1")
PORT = int(os.getenv("RADAR_PORT", "8000"))

# Scheduler configuration
DEFAULT_CHECK_INTERVAL_MINUTES = 30
RATE_LIMIT_DELAY_SECONDS = 0.5

# Candidate Profile Source of Truth: Technical Undergraduate Profile
CANDIDATE_PROFILE = {
    "name": "Undergraduate Candidate",
    "email": "candidate@example.com",
    "github": "https://github.com",
    "location": "India / Worldwide Remote",
    "citizenship": "India",
    "university": "B.Tech Computer Science (Data Science & AI)",
    "degree": "B.Tech",
    "major": "Computer Science (Data Science)",
    "education_level": "undergraduate",
    "start_year": 2025,
    "graduation_year": 2029,
    "cgpa": 9.15,
    "current_year": 2, # Second-year undergraduate in 2026-2027
    "target_internship_seasons": ["Summer 2027", "Fall 2026", "Winter 2026", "Spring 2027", "Summer 2026"],
    "primary_skills": [
        "PyTorch", "Triton", "CUDA", "GPU Kernels", "PyTorch Lightning", 
        "C++", "Python", "Language Modeling", "LLMs", "Transformers", 
        "GPU Optimization", "Distributed Training", "Operator Fusion", 
        "Newton-Schulz", "Muon", "AdamW", "FlashAttention", "GQA", "RoPE"
    ],
    "secondary_skills": [
        "FastAPI", "Docker", "SQL", "SQLAlchemy", "Flask", "Linux", 
        "LangChain", "LangGraph", "RAG", "Scikit-Learn", "Optuna", 
        "Tokenizers", "NumPy", "Pandas", "Matplotlib"
    ],
    "projects": [
        {
            "name": "PocketGPT: Efficient Language Modeling at 320M Parameters",
            "keywords": ["transformer", "decoder-only", "pretraining", "h100", "gqa", "rope", "rmsnorm", "qk-norm", "relu2", "muon", "adamw", "bpe", "lightning"],
            "description": "320M-parameter decoder-only Transformer from scratch in PyTorch & Lightning, trained on 5B tokens ClimbMix on H100. Outperformed Pythia-410M and GPT-2 Medium."
        },
        {
            "name": "Triton MuonAdamW: Custom GPU Kernels for Hybrid Optimization",
            "keywords": ["triton", "cuda", "gpu kernel", "fused", "optimization", "newton-schulz", "orthogonalization", "adamw", "muon", "matmul", "memory"],
            "description": "Hybrid optimizer on hand-written Triton kernels. Outperforms PyTorch built-in Muon by 1.27-1.30x. Fused Newton-Schulz orthogonalization and fused AdamW."
        },
        {
            "name": "FREUID Challenge 2026: ConvNeXt V2 Document Fraud Detection",
            "keywords": ["convnext", "computer vision", "classification", "optuna", "docker", "dataloader"],
            "description": "Fine-grained visual classification of manipulated documents using ConvNeXt V2, custom DataLoader, Docker inference, Optuna hyperparameter search."
        },
        {
            "name": "RIVAL-CAP DL Club Founder & LeetCode 450+",
            "keywords": ["deep learning research", "algorithms", "data structures", "c++", "competitive programming"],
            "description": "Founder & VP of university DL research & competitive programming club; solved 450+ LeetCode problems (175E, 251M, 24H)."
        }
    ],
    "priority_domains": [
        "GPU Kernel Engineering & Triton/CUDA Optimization",
        "LLM & Deep Learning Research",
        "ML Systems & Training Infrastructure",
        "Applied AI / ML Engineering",
        "High-Performance Backend & Distributed Systems"
    ]
}

# Registered source providers
DEFAULT_SOURCES = [
    {
        "id": "simplify_2026",
        "name": "SimplifyJobs Active Summer 2026 & Off-cycle Feed",
        "type": "live_feed",
        "url": "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "simplify_2027",
        "name": "SimplifyJobs Active Summer 2027 Feed",
        "type": "live_feed",
        "url": "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "nvidia_careers",
        "name": "NVIDIA Official Career API (Workday)",
        "type": "workday",
        "url": "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs",
        "company": "NVIDIA",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "cern_smartrecruiters",
        "name": "CERN openlab / Scientific Research (SmartRecruiters)",
        "type": "smartrecruiters",
        "url": "https://api.smartrecruiters.com/v1/companies/cern/postings",
        "company": "CERN",
        "enabled": True,
        "interval_minutes": 60
    },
    {
        "id": "greenhouse_anthropic",
        "name": "Anthropic Careers (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "anthropic",
        "company": "Anthropic",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "greenhouse_scaleai",
        "name": "Scale AI Careers (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "scaleai",
        "company": "Scale AI",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "greenhouse_databricks",
        "name": "Databricks Careers (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "databricks",
        "company": "Databricks",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "greenhouse_stripe",
        "name": "Stripe Careers (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "stripe",
        "company": "Stripe",
        "enabled": True,
        "interval_minutes": 45
    },
    {
        "id": "greenhouse_cloudflare",
        "name": "Cloudflare Careers (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "cloudflare",
        "company": "Cloudflare",
        "enabled": True,
        "interval_minutes": 45
    },
    {
        "id": "greenhouse_roblox",
        "name": "Roblox Careers (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "roblox",
        "company": "Roblox",
        "enabled": True,
        "interval_minutes": 45
    },
    {
        "id": "ashby_perplexity",
        "name": "Perplexity AI Careers (Ashby API)",
        "type": "ashby",
        "board_token": "perplexity",
        "company": "Perplexity",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "ashby_cursor",
        "name": "Cursor / Anysphere Careers (Ashby API)",
        "type": "ashby",
        "board_token": "cursor",
        "company": "Cursor",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "ashby_replit",
        "name": "Replit Careers (Ashby API)",
        "type": "ashby",
        "board_token": "replit",
        "company": "Replit",
        "enabled": True,
        "interval_minutes": 45
    },
    {
        "id": "ashby_baseten",
        "name": "Baseten LLM Serving (Ashby API)",
        "type": "ashby",
        "board_token": "baseten",
        "company": "Baseten",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "ashby_modal",
        "name": "Modal Labs GPU Cloud (Ashby API)",
        "type": "ashby",
        "board_token": "modal",
        "company": "Modal",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "ashby_supabase",
        "name": "Supabase Infra (Ashby API)",
        "type": "ashby",
        "board_token": "supabase",
        "company": "Supabase",
        "enabled": True,
        "interval_minutes": 45
    },
    {
        "id": "greenhouse_canonical",
        "name": "Canonical / Ubuntu (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "canonical",
        "company": "Canonical",
        "enabled": True,
        "interval_minutes": 45
    },
    {
        "id": "greenhouse_mongodb",
        "name": "MongoDB (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "mongodb",
        "company": "MongoDB",
        "enabled": True,
        "interval_minutes": 45
    },
    {
        "id": "greenhouse_elastic",
        "name": "Elastic Search & ML (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "elastic",
        "company": "Elastic",
        "enabled": True,
        "interval_minutes": 45
    },
    {
        "id": "greenhouse_gitlab",
        "name": "GitLab (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "gitlab",
        "company": "GitLab",
        "enabled": True,
        "interval_minutes": 45
    },
    {
        "id": "greenhouse_waymo",
        "name": "Waymo ML / Autonomous (Greenhouse API)",
        "type": "greenhouse",
        "board_token": "waymo",
        "company": "Waymo",
        "enabled": True,
        "interval_minutes": 45
    },
    {
        "id": "remoteok_ml",
        "name": "RemoteOK Developer & ML Jobs Feed",
        "type": "remoteok",
        "url": "https://remoteok.com/api",
        "enabled": True,
        "interval_minutes": 60
    },
    {
        "id": "wwr_programming",
        "name": "WeWorkRemotely Software & ML RSS",
        "type": "rss",
        "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "enabled": True,
        "interval_minutes": 60
    },
    {
        "id": "india_undergrad_feed",
        "name": "India Domestic Undergraduate Hub (LinkedIn/Campus)",
        "type": "india_feed",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "sarvam_ai",
        "name": "Sarvam AI Frontier LLM Lab (Bengaluru)",
        "type": "ashby",
        "board_token": "sarvam",
        "company": "Sarvam AI",
        "enabled": True,
        "interval_minutes": 30
    },
    {
        "id": "greenhouse_inmobi",
        "name": "InMobi AI & Systems (Bengaluru)",
        "type": "greenhouse",
        "board_token": "inmobi",
        "company": "InMobi",
        "enabled": True,
        "interval_minutes": 30
    }
]

# Internship Radar ⚡

> **High-Performance, Real-Time Undergraduate Internship Discovery Platform for GPU Computing, Deep Learning, ML Systems & Software Engineering.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL%20Mode-003B57.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Undergrad Verified](https://img.shields.io/badge/Undergraduate-100%25%20Verified-brightgreen.svg)]()

---

## 📌 Overview

**Internship Radar** is an automated, developer-first internship discovery engine and telemetry dashboard. It aggregates real-time technical undergraduate internship listings across **26+ direct ATS connectors and verified job feeds**, evaluates strict degree and graduation year eligibility, and scores opportunities against high-performance technical specializations.

### Core Focus Areas:
* 🚀 **GPU & Kernel Optimization:** OpenAI Triton, CUDA runtime, TensorRT, ROCm, custom GEMM / FlashAttention / RMSNorm / fused optimizers.
* 🧠 **LLM Research & Modeling:** Decoder-only Transformer pretraining, RoPE, GQA, scaling laws, deep learning training dynamics.
* ⚙️ **ML Systems & Training Infra:** PyTorch Lightning, distributed training (FSDP, DeepSpeed), memory-efficient data ingestion, operator fusion.
* 🔬 **Applied Deep Learning & Vision:** ConvNeXt, fine-grained classification, hyperparameter tuning with Optuna, Docker inference.
* 💻 **Backend & Distributed Systems:** High-throughput FastAPI, C++, Linux systems programming, Docker, algorithms and data structures.

---

## 🌟 Key Features

* **Strict 100% Undergraduate Verification (Zero PhD / Master's Leakage):**
  * Multi-layer query and regex screening engine completely disqualifies graduate, PhD, doctoral, MBA, and post-graduate requirements.
  * Disqualifies senior and regular full-time positions to ensure every listing is an internship, co-op, or student fellowship.
* **Multi-Source ATS & Board Connectors (26 Active Sources):**
  * **Direct ATS Connectors:** Ashby, Greenhouse, Workday, SmartRecruiters.
  * **Frontier AI Labs & Tech Leaders:** NVIDIA, Anthropic, Scale AI, Databricks, Stripe, Cloudflare, Roblox, CERN openlab, Sarvam AI, and more.
  * **Aggregated Engineering Feeds:** SimplifyJobs Summer 2026/2027, India Domestic Engineering Hub, WeWorkRemotely, RemoteOK.
* **Geographic Accuracy & Domestic Hubs:**
  * Dedicated filtering for Indian tech centers (**Bengaluru, Hyderabad, Pune, Mumbai, Gurgaon, Noida, Chennai**).
  * Substring collision prevention (eliminating false-positives such as "Indianapolis, IN").
  * Global Remote tagging and international visa/sponsorship qualification badges.
* **Automated Cold Outreach Pitch Generator:**
  * Built-in context generator that drafts personalized, high-signal cold outreach notes directly referencing technical projects and domain skills for recruiters and engineering leads.
* **Fast, Minimalist Command Center UI:**
  * Dark, sharp, high-density dashboard built for technical users.
  * Interactive telemetry widgets with live counts, 7-day sparklines, and domain distribution bars.
  * Keyboard navigation (`/` search, `J`/`K` navigation, `S` bookmark, `A` apply).
  * Fast pipeline tracking (`Track`, `Remove`, `Archive`, `Restore`).

---

## 🛠️ Project Architecture

```
internship-radar/
├── backend/
│   ├── main.py              # FastAPI app lifecycle and server mount
│   ├── api.py               # REST endpoints (/stats, /listings, /pitch, /sources)
│   ├── config.py            # Candidate profile, scheduler intervals, source definitions
│   ├── database.py          # SQLite connection manager, WAL mode, schema init
│   ├── collector.py         # Multi-threaded background collection pipeline
│   ├── scheduler.py         # Periodic background refresh cron
│   ├── eligibility.py       # Strict undergraduate validation & graduation-year filters
│   ├── matching.py          # Relevance scoring engine & skill clustering
│   ├── deduplication.py     # Deterministic SHA256 canonical URL & title hashing
│   └── connectors/          # Source integrations
│       ├── ashby.py         # Ashby ATS posting API connector
│       ├── greenhouse.py    # Greenhouse board API connector
│       ├── workday.py       # Workday careers search API connector
│       ├── smartrecruiters.py # SmartRecruiters openlab connector
│       ├── india_internships.py # Indian domestic tech feeds & Sarvam AI
│       ├── live_feed.py     # GitHub JSON internship feeds
│       └── remote_rss.py    # RemoteOK and WeWorkRemotely RSS feeds
├── frontend/
│   ├── index.html           # Command center single-page dashboard
│   ├── app.js               # Reactive state manager, modal logic, keyboard shortcuts
│   └── styles.css           # Minimalist dark theme & animations
├── data/
│   └── internships.db       # SQLite database with indexed, vetted listings
├── scripts/
│   ├── start_dashboard.bat  # One-click Windows launcher
│   ├── start_silent.vbs     # Silent background execution script
│   ├── install_shortcut.py  # Desktop shortcut installer
│   └── purge_non_internships.py # Database cleanup and validation utility
├── tests/                   # Pytest test suite (eligibility, matching, deduplication)
├── requirements.txt         # Production dependencies
└── config.json              # Configurable runtime parameters
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
* **Python 3.10+**
* **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/Mithun-033/Internship-radar.git
cd Internship-radar
```

### 3. Create a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On Linux / macOS / WSL:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Start the Server
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## ⚙️ Customizing Your Profile

The scoring engine, recommendation weights, and cold pitch generator adapt dynamically to your technical profile.

To customize the candidate profile with your own skills, projects, and graduation year:

1. Open `backend/config.py` (or `config.json`).
2. Update the `CANDIDATE_PROFILE` dictionary:

```python
CANDIDATE_PROFILE = {
    "name": "Your Name",
    "email": "your.email@example.com",
    "github": "https://github.com/your-handle",
    "location": "Your City, Country",
    "citizenship": "Your Country",
    "university": "Your University",
    "degree": "B.Tech / B.S.",
    "major": "Computer Science",
    "graduation_year": 2029,
    "primary_skills": [
        "PyTorch", "Triton", "CUDA", "C++", "Python", "LLMs"
    ],
    "projects": [
        {
            "name": "Your Key Project Name",
            "keywords": ["gpu", "cuda", "transformer", "pytorch"],
            "description": "Brief summary of your project and technical impact."
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
```

Restart the server to immediately re-evaluate match scores across all active listings.

---

## 🧪 Running Tests

The test suite validates deduplication algorithms, date verification (Asia/Kolkata timezone rollover), strict undergraduate qualification rules, and match scoring tiers.

```bash
python -m pytest tests -v
```

Expected output:
```
tests/test_database.py::test_database_init_and_sources_population PASSED
tests/test_deduplication.py::test_deterministic_listing_id_deduplication PASSED
tests/test_eligibility.py::test_reject_phd_only_roles PASSED
tests/test_eligibility.py::test_reject_masters_and_doctoral_roles PASSED
tests/test_eligibility.py::test_reject_full_time_actual_jobs PASSED
tests/test_matching.py::test_gpu_triton_highest_tier PASSED
...
============================= 22 passed in 0.30s ==============================
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| `/` | Focus search bar |
| `Esc` | Clear search / close open modal |
| `J` / `K` | Select next / previous listing card |
| `S` | Toggle bookmark on selected listing |
| `A` | Open official application link in new tab |

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

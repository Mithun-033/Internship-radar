"""
Resume-based relevance scoring and matching engine.
Evaluates listings against the candidate's technical profile, projects, and skills.
"""
import re
from typing import Dict, Any, List, Tuple
from .config import CANDIDATE_PROFILE

SKILL_PATTERNS = {
    "Triton": [r'\btriton\b'],
    "CUDA": [r'\bcuda\b', r'\bgpu\s+computing\b'],
    "GPU Kernels": [r'\bgpu\s+kernels?\b', r'\bkernel\s+(?:optimization|development)\b', r'\baccelerated\s+computing\b'],
    "PyTorch": [r'\bpytorch\b', r'\btorch\b'],
    "PyTorch Lightning": [r'\bpytorch\s+lightning\b', r'\blightning\b'],
    "C++": [r'\bc\+\+\b', r'\bcpp\b'],
    "Python": [r'\bpython\b'],
    "LLMs": [r'\bllms?\b', r'\blarge\s+language\s+models?\b', r'\bgenerative\s+ai\b', r'\bdecoder-only\b'],
    "Transformers": [r'\btransformers?\b', r'\battention\b', r'\bgqa\b', r'\brope\b'],
    "ML Systems": [r'\bml\s+systems\b', r'\bai\s+infrastructure\b', r'\btraining\s+infrastructure\b', r'\binference\s+engine\b', r'\bvllm\b', r'\btensorrt\b'],
    "Distributed Training": [r'\bdistributed\s+(?:training|systems)\b', r'\bdeepspeed\b', r'\bmegatron\b', r'\bfsdp\b'],
    "Computer Vision": [r'\bcomputer\s+vision\b', r'\bimage\s+classification\b', r'\bconvnext\b'],
    "FastAPI": [r'\bfastapi\b'],
    "Docker": [r'\bdocker\b', r'\bcontainers?\b', r'\bcontainerization\b'],
    "SQL / Databases": [r'\bsql\b', r'\bsqlalchemy\b', r'\bpostgres\b', r'\bdatabase\b'],
    "Optuna": [r'\boptuna\b', r'\bhyperparameter\s+tuning\b'],
    "Compilers": [r'\bcompilers?\b', r'\bllvm\b', r'\bmlir\b', r'\boperator\s+fusion\b']
}

COMMON_TECH_STACK_MISSING = [
    ("Kubernetes", r'\bkubernetes\b|\bk8s\b'),
    ("Rust", r'\brust\b'),
    ("Go / Golang", r'\bgolang\b|\bgo\s+developer\b'),
    ("AWS / Cloud Infra", r'\baws\b|\bazure\b|\bgcp\b'),
    ("React / Frontend", r'\breact\b|\bfrontend\b|\btypescript\b'),
    ("Robotics / ROS", r'\bros\b|\brobotics\b')
]

def score_listing(listing: Dict[str, Any]) -> Tuple[int, str, List[str], List[str], List[str], List[str]]:
    """
    Computes a 0-100 score, category, match reasons, matched skills, matched projects, and skill gaps.
    """
    title = (listing.get("title") or "").lower()
    desc = (listing.get("description_snippet") or "").lower()
    comp = (listing.get("company") or "").lower()
    full_text = f"{title} {desc} {comp}"

    matched_skills = []
    for skill_name, patterns in SKILL_PATTERNS.items():
        if any(re.search(p, full_text) for p in patterns):
            matched_skills.append(skill_name)

    matched_projects = []
    missing_skills = []

    # Detect missing requirements
    for tech_name, pat in COMMON_TECH_STACK_MISSING:
        if re.search(pat, full_text):
            missing_skills.append(tech_name)

    # 1. Tier 1: GPU Kernel Engineering, Triton, CUDA, Accelerated Computing
    gpu_matches = [s for s in matched_skills if s in ["Triton", "CUDA", "GPU Kernels", "Compilers"]]
    is_gpu = bool(gpu_matches) or any(k in full_text for k in ["gpu", "cuda", "triton", "kernel", "compiler", "cutlass", "accelerat"])
    
    # 2. Tier 2: LLM Research, Language Modeling, Deep Learning Research
    llm_matches = [s for s in matched_skills if s in ["LLMs", "Transformers", "PyTorch", "PyTorch Lightning"]]
    is_llm = bool(re.search(r'\b(llm|language model|pretraining|transformer|reasoning|foundation model|deep learning research|ai research)\b', full_text))

    # 3. Tier 3: ML Systems, Training Infra, Efficient Inference
    is_ml_sys = bool(re.search(r'\b(ml systems|ai infrastructure|inference|distributed training|gpu cluster|training platform|deep learning systems)\b', full_text))

    # 4. Tier 4: Applied AI / ML Engineering
    is_applied_ml = bool(re.search(r'\b(machine learning|deep learning|data science|applied ml|computer vision|nlp|model)\b', full_text))

    # 5. Tier 5: High-Performance Backend & Distributed Systems
    is_backend = bool(re.search(r'\b(backend|distributed systems|systems engineer|software engineer|infrastructure|c\+\+|fastapi|docker)\b', full_text))

    reasons = []
    score = 50
    category = "General Engineering"

    if is_gpu and ("kernel" in full_text or "cuda" in full_text or "triton" in full_text or "compiler" in full_text or "accelerat" in full_text):
        category = "GPU & Triton Optimization"
        score = 92
        matched_projects.append("Triton MuonAdamW: Custom GPU Kernels for Hybrid Optimization (1.27-1.30x speedup over PyTorch built-in, fused Newton-Schulz)")
        reasons.append("Top Priority Match: Directly targets candidate's core specialization in custom Triton/CUDA GPU kernels and memory-efficient operator fusion.")
        if "C++" in matched_skills:
            score += 4
        if "Triton" in matched_skills:
            score += 3
    elif is_llm and ("research" in full_text or "model" in full_text or "pretraining" in full_text or "transformer" in full_text):
        category = "LLM Research & Modeling"
        score = 88
        matched_projects.append("PocketGPT: 320M Parameter Decoder-Only Transformer (trained from scratch on H100 with ClimbMix, RoPE, RMSNorm, GQA, QK-Norm)")
        reasons.append("Exceptional Match: Direct alignment with candidate's hands-on decoder-only transformer pretraining and modern architectural stack.")
        if "PyTorch" in matched_skills:
            score += 4
        if "Transformers" in matched_skills:
            score += 3
    elif is_ml_sys:
        category = "ML Systems & Training Infra"
        score = 82
        matched_projects.append("PocketGPT & Triton MuonAdamW: End-to-end memory-mapped training loops, optimizer kernel fusion, and PyTorch Lightning pipelines.")
        reasons.append("High Alignment: Matches candidate's experience in building scalable training infrastructure and GPU optimizer efficiency.")
        if "PyTorch" in matched_skills:
            score += 4
        if "Docker" in matched_skills:
            score += 3
    elif is_applied_ml:
        category = "Applied AI / ML"
        score = 74
        matched_projects.append("FREUID Challenge 2026: ConvNeXt V2 Image Classification with custom DataLoader and Optuna hyperparameter optimization.")
        reasons.append("Strong Fit: Leverages deep learning modeling, PyTorch workflows, and automated hyperparameter tuning.")
        if "PyTorch" in matched_skills:
            score += 4
    elif is_backend or "software" in title:
        category = "Backend & Systems"
        score = 65
        matched_projects.append("IBM Back-End Development Professional Certificate & 450+ LeetCode problems solved across C++ and Python.")
        reasons.append("Solid Engineering Alignment: Relevant to candidate's skills in FastAPI, C++, SQL, Docker, and algorithmic problem-solving.")
        if "C++" in matched_skills or "FastAPI" in matched_skills:
            score += 5
    else:
        category = "General Engineering"
        score = 52
        matched_projects.append("Competitive Programming & CS Core: 450+ LeetCode problems solved; Computer Science curriculum.")
        reasons.append("General CS / Software Internship: Candidate has strong fundamentals in Python, C++, and algorithms.")

    # Cap score
    score = max(30, min(99, score))

    # Add default matched skills if list was empty
    if not matched_skills:
        matched_skills = ["Python", "C++"]

    return score, category, reasons, matched_skills, matched_projects, missing_skills

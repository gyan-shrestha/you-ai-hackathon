"""
query_builder.py
Automatically builds optimized You.com search queries from user questions.
"""

import re
import json
from typing import Dict, Tuple, List
from utils.you_api_utils import search_pdfs

# ---------------------------------------------------------------------
# Load domain mapping
# ---------------------------------------------------------------------
with open("insurer_domains.json") as f:
    INSURER_DOMAINS = json.load(f)

# ---------------------------------------------------------------------
# Feature and Insurer Detectors
# ---------------------------------------------------------------------
def detect_insurer(text: str) -> str:
    for name in INSURER_DOMAINS.keys():
        if name.lower() in text.lower():
            return name
    return "HealthCare.gov"

def detect_feature(text: str) -> str:
    mapping = {
        "deduct": "deductible",
        "premium": "premium",
        "copay": "copay",
        "out-of-pocket": "out of pocket maximum",
        "coverage": "coverage"
    }
    for k, v in mapping.items():
        if k in text.lower():
            return v
    return "benefits"

def detect_year(text: str) -> int:
    m = re.search(r"(20\d{2})", text)
    return int(m.group(1)) if m else 2025

def detect_plan(text: str) -> str:
    m = re.search(r"(Silver|Gold|Bronze|Platinum)\s?[\w\s\-]*", text, re.IGNORECASE)
    return m.group(0).strip() if m else "Marketplace Plan"

def get_site_from_insurer(insurer_name: str) -> str:
    for k, domains in INSURER_DOMAINS.items():
        if k.lower() in insurer_name.lower():
            return domains[0]
    return "healthcare.gov"

# ---------------------------------------------------------------------
# Query Builder
# ---------------------------------------------------------------------
def build_and_search(user_question: str) -> Tuple[str, List[str]]:
    insurer = detect_insurer(user_question)
    plan = detect_plan(user_question)
    year = detect_year(user_question)

    domain = get_site_from_insurer(insurer)
    fallbacks = ["healthcare.gov", "cms.gov"]

    # Extract normalized metal tier and plan type
    metal_tier = ""
    plan_type = ""
    if "silver" in plan.lower():
        metal_tier = "Silver"
    elif "gold" in plan.lower():
        metal_tier = "Gold"
    elif "bronze" in plan.lower():
        metal_tier = "Bronze"
    elif "platinum" in plan.lower():
        metal_tier = "Platinum"

    if "ppo" in plan.lower():
        plan_type = "PPO"
    elif "hmo" in plan.lower():
        plan_type = "HMO"

    # Build optimized You.com query
    # base_query = f'site:{domain} "Summary of Benefits and Coverage" {year} {metal_tier} {plan_type} Florida'
    base_query = f'site:{domain} {year} {metal_tier} {plan_type} Florida'

    for site in [domain] + fallbacks:
        query = base_query.replace(domain, site)
        print(f"Trying query: {query}")
        results = search_pdfs(query)

        if results:
            print(f"Found {len(results)} result(s) from {site}")
            return query, results

    print("No PDFs found for any site.")
    return "", []

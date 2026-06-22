"""
Synthetic Evaluation Suite
============================
Career & University Recommendation System

Evaluates the recommendation engine using synthetic user profiles
with expert-defined expected outcomes.

Metrics:
- Precision@K: % of recommendations that are relevant
- Coverage: % of programs/universities that get recommended
- Diversity: How diverse are the recommendations (major groups, provinces)
- Safety Distribution: Mix of safe/moderate/reach programs
- Score Feasibility: % of recommendations where user can actually get admitted
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from typing import Dict, List, Any
from collections import Counter

from data_loader import DataLoader
from recommender import RecommendationEngine, UserProfile, print_recommendations


# ──────────────────────────────────────────
# Synthetic Test Profiles
# ──────────────────────────────────────────

SYNTHETIC_PROFILES = [
    {
        "name": "Khá Tự Nhiên - Hà Nội",
        "profile": UserProfile(
            exam_block=["A00", "A01"],
            total_score=24.0,
            province="Hà Nội",
            preferred_provinces=["Hà Nội"],
            interest_keywords=["kỹ thuật", "công nghệ", "máy tính"],
            major_group_names=["Khoa học máy tính - Kỹ thuật phần mềm"],
        ),
        "expected_groups": ["Khoa học máy tính - Kỹ thuật phần mềm"],
        "expected_provinces": ["Hà Nội"],
        "min_score": 18.0,
        "max_score": 27.0,
    },
    {
        "name": "Giỏi Xã Hội - TP.HCM",
        "profile": UserProfile(
            exam_block=["D01", "C00"],
            total_score=27.0,
            province="TP.HCM",
            preferred_provinces=["TP.HCM"],
            interest_keywords=["kinh doanh", "quản trị", "marketing"],
            major_group_names=["Kinh tế - Quản trị kinh doanh"],
        ),
        "expected_groups": ["Kinh tế - Quản trị kinh doanh", "Kế toán - Kiểm toán"],
        "expected_provinces": ["TP.HCM"],
        "min_score": 22.0,
        "max_score": 30.0,
    },
    {
        "name": "Trung Bình - Đà Nẵng - Budget",
        "profile": UserProfile(
            exam_block=["A00"],
            total_score=18.5,
            province="Đà Nẵng",
            budget_max=25_000_000,
            preferred_provinces=["Đà Nẵng", "Huế"],
            university_type="Công lập",
        ),
        "expected_groups": [],  # Any group OK
        "expected_provinces": ["Đà Nẵng", "Huế"],
        "min_score": 14.0,
        "max_score": 21.5,
    },
    {
        "name": "Xuất sắc - Y Dược",
        "profile": UserProfile(
            exam_block=["B00"],
            total_score=28.5,
            province="Hà Nội",
            preferred_provinces=["Hà Nội", "TP.HCM", "Huế"],
            interest_keywords=["y khoa", "dược", "y tế"],
            major_group_names=["Y - Dược"],
        ),
        "expected_groups": ["Y - Dược"],
        "expected_provinces": ["Hà Nội", "TP.HCM", "Huế"],
        "min_score": 24.0,
        "max_score": 30.0,
    },
    {
        "name": "Khá - Sư Phạm - Tỉnh lẻ",
        "profile": UserProfile(
            exam_block=["A00", "A01", "D01"],
            total_score=22.0,
            province="Thanh Hóa",
            budget_max=15_000_000,
            interest_keywords=["sư phạm", "giáo dục", "dạy học"],
            major_group_names=["Sư phạm"],
        ),
        "expected_groups": ["Sư phạm"],
        "expected_provinces": [],  # Any province OK
        "min_score": 16.0,
        "max_score": 25.0,
    },
    {
        "name": "Cold Start - Chỉ Level 1",
        "profile": UserProfile(
            exam_block=["A00"],
            total_score=20.0,
            province="Nghệ An",
        ),
        "expected_groups": [],
        "expected_provinces": ["Nghệ An"],
        "min_score": 14.0,
        "max_score": 23.0,
    },
    {
        "name": "Giỏi - Ngôn Ngữ Anh",
        "profile": UserProfile(
            exam_block=["D01"],
            total_score=26.0,
            province="Hà Nội",
            preferred_provinces=["Hà Nội", "TP.HCM"],
            interest_keywords=["ngôn ngữ", "tiếng anh", "phiên dịch", "du lịch"],
            major_group_names=["Ngôn ngữ - Ngoại ngữ"],
        ),
        "expected_groups": ["Ngôn ngữ - Ngoại ngữ"],
        "expected_provinces": ["Hà Nội", "TP.HCM"],
        "min_score": 20.0,
        "max_score": 29.0,
    },
    {
        "name": "Trung Bình Khá - Xây Dựng",
        "profile": UserProfile(
            exam_block=["A00", "A01"],
            total_score=21.0,
            province="Hải Phòng",
            preferred_provinces=["Hà Nội", "Hải Phòng"],
            interest_keywords=["xây dựng", "kiến trúc", "kỹ thuật"],
            major_group_names=["Xây dựng - Kiến trúc"],
        ),
        "expected_groups": ["Xây dựng - Kiến trúc"],
        "expected_provinces": ["Hà Nội", "Hải Phòng"],
        "min_score": 15.0,
        "max_score": 24.0,
    },
]


# ──────────────────────────────────────────
# Evaluation Functions
# ──────────────────────────────────────────

def evaluate_profile(engine: RecommendationEngine, test_case: Dict, top_k: int = 10) -> Dict[str, Any]:
    """Evaluate recommendations for a single test profile."""
    result = engine.recommend(test_case["profile"], top_k=top_k)
    recs = result["recommendations"]
    meta = result["metadata"]
    
    metrics = {
        "name": test_case["name"],
        "candidates": meta["after_filter"],
        "returned": len(recs),
    }
    
    if not recs:
        metrics.update({
            "interest_precision": 0.0,
            "location_precision": 0.0,
            "score_feasibility": 0.0,
            "unique_universities": 0,
            "unique_major_groups": 0,
            "unique_provinces": 0,
            "safety_distribution": {},
        })
        return metrics

    # Interest Precision: % of recs in expected major groups
    expected_groups = test_case.get("expected_groups", [])
    if expected_groups:
        interest_hits = sum(
            1 for r in recs 
            if r.get("major_group_name") in expected_groups
        )
        metrics["interest_precision"] = interest_hits / len(recs)
    else:
        metrics["interest_precision"] = None  # N/A

    # Location Precision: % of recs in expected provinces
    expected_provinces = test_case.get("expected_provinces", [])
    if expected_provinces:
        location_hits = sum(
            1 for r in recs
            if r.get("province") in expected_provinces
        )
        metrics["location_precision"] = location_hits / len(recs)
    else:
        metrics["location_precision"] = None

    # Score Feasibility: % of recs where latest_score <= total_score + margin
    user_score = test_case["profile"].total_score
    score_feasible = sum(
        1 for r in recs
        if r.get("latest_score_thpt") is None or
           r.get("latest_score_thpt") <= user_score + 3
    )
    metrics["score_feasibility"] = score_feasible / len(recs)

    # Diversity metrics
    metrics["unique_universities"] = len(set(r.get("university_code") for r in recs if r.get("university_code")))
    metrics["unique_major_groups"] = len(set(r.get("major_group_name") for r in recs if r.get("major_group_name")))
    metrics["unique_provinces"] = len(set(r.get("province") for r in recs if r.get("province")))

    # Safety distribution
    safety_counts = Counter(r.get("safety_level", "unknown") for r in recs)
    metrics["safety_distribution"] = dict(safety_counts)

    return metrics


def run_full_evaluation(engine: RecommendationEngine, top_k: int = 10):
    """Run evaluation across all synthetic profiles and compute aggregate metrics."""
    
    print(f"\n{'='*80}")
    print(f"  SYNTHETIC EVALUATION SUITE")
    print(f"  Profiles: {len(SYNTHETIC_PROFILES)} | Top-K: {top_k}")
    print(f"{'='*80}\n")

    all_metrics = []
    all_recommended_programs = set()
    all_recommended_universities = set()

    for i, test_case in enumerate(SYNTHETIC_PROFILES, 1):
        print(f"  [{i}/{len(SYNTHETIC_PROFILES)}] Evaluating: {test_case['name']}...")
        metrics = evaluate_profile(engine, test_case, top_k)
        all_metrics.append(metrics)

        # Collect coverage data
        result = engine.recommend(test_case["profile"], top_k=top_k)
        for r in result["recommendations"]:
            if r.get("program_id"):
                all_recommended_programs.add(str(r["program_id"]))
            if r.get("university_code"):
                all_recommended_universities.add(r["university_code"])

    # ── Per-profile results ──
    print(f"\n{'='*80}")
    print(f"  PER-PROFILE RESULTS")
    print(f"{'='*80}\n")
    
    headers = ["Profile", "Cands", "Recs", "Int.Prec", "Loc.Prec", "Feasib.", "Uni#", "Grp#", "Safety"]
    rows = []
    for m in all_metrics:
        ip = f"{m['interest_precision']:.0%}" if m['interest_precision'] is not None else "N/A"
        lp = f"{m['location_precision']:.0%}" if m['location_precision'] is not None else "N/A"
        sf = f"{m['score_feasibility']:.0%}"
        safety = "|".join(f"{k[0]}:{v}" for k, v in sorted(m['safety_distribution'].items()))
        rows.append([
            m["name"][:30], m["candidates"], m["returned"],
            ip, lp, sf, m["unique_universities"], m["unique_major_groups"], safety
        ])

    # Print as table
    col_widths = [max(len(str(r[j])) for r in rows + [headers]) for j in range(len(headers))]
    header_str = " | ".join(f"{h:<{col_widths[j]}}" for j, h in enumerate(headers))
    print(f"  {header_str}")
    print(f"  {'-' * len(header_str)}")
    for row in rows:
        row_str = " | ".join(f"{str(v):<{col_widths[j]}}" for j, v in enumerate(row))
        print(f"  {row_str}")

    # ── Aggregate metrics ──
    print(f"\n{'='*80}")
    print(f"  AGGREGATE METRICS")
    print(f"{'='*80}\n")

    # Interest precision (excluding N/A)
    ip_values = [m["interest_precision"] for m in all_metrics if m["interest_precision"] is not None]
    avg_ip = np.mean(ip_values) if ip_values else 0
    
    # Location precision (excluding N/A)
    lp_values = [m["location_precision"] for m in all_metrics if m["location_precision"] is not None]
    avg_lp = np.mean(lp_values) if lp_values else 0
    
    # Score feasibility
    sf_values = [m["score_feasibility"] for m in all_metrics]
    avg_sf = np.mean(sf_values)
    
    # Coverage
    total_programs = len(engine.catalog)
    total_universities = engine.catalog["university_code"].nunique()
    program_coverage = len(all_recommended_programs) / total_programs if total_programs > 0 else 0
    uni_coverage = len(all_recommended_universities) / total_universities if total_universities > 0 else 0
    
    # Average diversity
    avg_uni_diversity = np.mean([m["unique_universities"] for m in all_metrics])
    avg_grp_diversity = np.mean([m["unique_major_groups"] for m in all_metrics])

    print(f"  {'Metric':<35} {'Value':<15} {'Target':<15} {'Status'}")
    print(f"  {'-'*80}")
    print(f"  {'Avg Interest Precision':<35} {avg_ip:<15.1%} {'≥ 40%':<15} {'✅' if avg_ip >= 0.4 else '⚠️'}")
    print(f"  {'Avg Location Precision':<35} {avg_lp:<15.1%} {'≥ 50%':<15} {'✅' if avg_lp >= 0.5 else '⚠️'}")
    print(f"  {'Avg Score Feasibility':<35} {avg_sf:<15.1%} {'≥ 90%':<15} {'✅' if avg_sf >= 0.9 else '⚠️'}")
    print(f"  {'Program Coverage':<35} {program_coverage:<15.1%} {'≥ 5%':<15} {'✅' if program_coverage >= 0.05 else '⚠️'}")
    print(f"  {'University Coverage':<35} {uni_coverage:<15.1%} {'≥ 10%':<15} {'✅' if uni_coverage >= 0.1 else '⚠️'}")
    print(f"  {'Avg Uniq Universities/Profile':<35} {avg_uni_diversity:<15.1f} {'≥ 3':<15} {'✅' if avg_uni_diversity >= 3 else '⚠️'}")
    print(f"  {'Avg Uniq Major Groups/Profile':<35} {avg_grp_diversity:<15.1f} {'≥ 2':<15} {'✅' if avg_grp_diversity >= 2 else '⚠️'}")

    # Overall safety distribution
    total_safety = Counter()
    for m in all_metrics:
        total_safety.update(m["safety_distribution"])
    total_recs = sum(total_safety.values())
    
    print(f"\n  Safety Level Distribution (across all profiles):")
    for level in ["safe", "moderate", "reach", "ambitious", "unknown"]:
        count = total_safety.get(level, 0)
        pct = count / total_recs * 100 if total_recs > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"    {level:<12} {count:>4} ({pct:>5.1f}%) {bar}")

    print(f"\n{'='*80}")
    overall_pass = avg_sf >= 0.9 and avg_ip >= 0.3
    print(f"  OVERALL: {'✅ PASS' if overall_pass else '⚠️ NEEDS TUNING'}")
    print(f"{'='*80}\n")

    return all_metrics


if __name__ == "__main__":
    print("Loading data...")
    loader = DataLoader()
    catalog = loader.build_program_catalog()
    engine = RecommendationEngine(catalog)
    
    print(f"Catalog: {len(catalog):,} programs")
    
    run_full_evaluation(engine, top_k=10)

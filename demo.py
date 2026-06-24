"""
Demo Script — Career & University Recommendation System
========================================================
Tests the recommendation engine with sample user profiles.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

from data_loader import DataLoader
from recommender import RecommendationEngine, UserProfile, print_recommendations
from personality_mapper import calculate_numerology, get_zodiac_sign


def main():
    print("=" * 80)
    print("  LOADING DATA...")
    print("=" * 80)
    
    loader = DataLoader()
    catalog = loader.build_program_catalog()
    
    print(f"  ✅ Loaded {len(catalog):,} programs")
    print(f"  ✅ {catalog['latest_score_thpt'].notna().sum():,} have THPT scores")
    print(f"  ✅ {catalog['major_group_name'].notna().sum():,} have major group names")
    
    engine = RecommendationEngine(catalog)
    
    # ──────────────────────────────────────────
    # Test Case 1: Học sinh khá, khối A00, Hà Nội
    # ──────────────────────────────────────────
    print("\n\n" + "█" * 80)
    print("  TEST CASE 1: Học sinh khá - Khối A00 - Hà Nội")
    print("█" * 80)
    
    user1 = UserProfile(
        exam_block=["A00"],
        total_score=24.5,
        subject_scores={"Toán": 8.5, "Vật lý": 8.0, "Hóa học": 8.0},
        interest_keywords=["công nghệ", "phần mềm", "máy tính", "kỹ thuật"],
        major_group_names=["Khoa học máy tính - Kỹ thuật phần mềm"],
    )
    
    result1 = engine.recommend(user1, top_k=10)
    print_recommendations(result1)

    # ──────────────────────────────────────────
    # Test Case 2: Học sinh giỏi, khối D01, TP.HCM, budget limited
    # ──────────────────────────────────────────
    print("\n\n" + "█" * 80)
    print("  TEST CASE 2: Học sinh giỏi - Khối D01 - TP.HCM - Budget hạn chế")
    print("█" * 80)
    
    user2 = UserProfile(
        exam_block=["D01"],
        total_score=27.0,
        subject_scores={"Toán": 9.0, "Văn": 8.5, "Tiếng Anh": 9.5},
        budget_max=30_000_000,  # 30 triệu/năm
        university_type="Công lập",
        interest_keywords=["kinh doanh", "quản trị", "tài chính", "marketing"],
        major_group_names=["Kinh tế - Quản trị kinh doanh", "Kế toán - Kiểm toán"],
    )
    
    result2 = engine.recommend(user2, top_k=10)
    print_recommendations(result2)

    # ──────────────────────────────────────────
    # Test Case 3: Học sinh trung bình, tỉnh lẻ, chưa biết ngành
    # (Cold Start - Level 1 only)
    # ──────────────────────────────────────────
    print("\n\n" + "█" * 80)
    print("  TEST CASE 3: Cold Start - Chỉ có thông tin cơ bản")
    print("█" * 80)
    
    user3 = UserProfile(
        exam_block=["A00", "A01"],
        total_score=20.0,
    )
    
    result3 = engine.recommend(user3, top_k=10)
    print_recommendations(result3)

    # ──────────────────────────────────────────
    # Test Case 4: Học sinh muốn ngành Y, điểm rất cao
    # ──────────────────────────────────────────
    print("\n\n" + "█" * 80)
    print("  TEST CASE 4: Ngành Y Dược - Điểm cao")
    print("█" * 80)
    
    user4 = UserProfile(
        exam_block=["B00"],
        total_score=28.5,
        subject_scores={"Toán": 9.5, "Hóa học": 9.5, "Sinh học": 9.5},
        interest_keywords=["y khoa", "dược", "y tế", "sức khỏe"],
        major_group_names=["Y - Dược"],
    )
    
    result4 = engine.recommend(user4, top_k=10)
    print_recommendations(result4)

    # ──────────────────────────────────────────
    # Test Case 5: Flow Phòng thi thử (Mock Exam)
    # ──────────────────────────────────────────
    print("\n\n" + "█" * 80)
    print("  TEST CASE 5: Flow Phòng thi thử - Có Nguyện vọng cụ thể")
    print("█" * 80)
    
    dob5 = "2006-08-15"
    user5 = UserProfile(
        flow_type="mock_exam",
        exam_block=["A00"],
        total_score=25.0,
        current_score=24.5,
        numerology=calculate_numerology(dob5),
        zodiac=get_zodiac_sign(dob5),
        aspirations=[
            {"university_code": "BKA", "major_name": "Công nghệ thông tin"},
            {"university_code": "FTU", "major_name": "Kinh tế quốc tế"}
        ]
    )
    
    result5 = engine.recommend(user5, top_k=5)
    print_recommendations(result5)
    print("\n  [Aspiration Matches - % Phù hợp ngành]:")
    for a in result5.get("aspiration_matches", []):
        print(f"   -> {a['major_name']} ({a['major_group_name']}): {a['match_percentage']}%")

    # ──────────────────────────────────────────
    # Test Case 6: Flow Khám phá bản thân (Discovery - Có Holland)
    # ──────────────────────────────────────────
    print("\n\n" + "█" * 80)
    print("  TEST CASE 6: Flow Khám phá bản thân - Có test Holland")
    print("█" * 80)
    
    dob6 = "2006-03-05"
    user6 = UserProfile(
        flow_type="discovery",
        exam_block=["A01"],
        total_score=24.0,
        holland_code="SIA",
        numerology=calculate_numerology(dob6),
        zodiac=get_zodiac_sign(dob6),
        aspirations=[
            {"university_code": "VNU", "major_name": "Tâm lý học"}
        ]
    )
    
    result6 = engine.recommend(user6, top_k=5)
    print_recommendations(result6)
    print("\n  [Aspiration Matches - % Phù hợp ngành]:")
    for a in result6.get("aspiration_matches", []):
        print(f"   -> {a['major_name']} ({a['major_group_name']}): {a['match_percentage']}%")

    # ──────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  ALL TEST CASES COMPLETED")
    print("=" * 80)
    for i, result in enumerate([result1, result2, result3, result4, result5, result6], 1):
        meta = result["metadata"]
        recs = result.get("recommendations", [])
        safety = meta.get("safety_distribution", {})
        print(f"  Test {i}: {meta['after_filter']:,} candidates → {len(recs)} recommendations | Safety: {safety}")


if __name__ == "__main__":
    main()

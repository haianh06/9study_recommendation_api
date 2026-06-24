def print_recommendations(result: dict):
    """Helper to pretty-print recommendation results"""
    if "top_majors" in result and result["top_majors"]:
        print("\n  [Top Major Groups Match]:")
        for m in result["top_majors"]:
            print(f"   -> {m['major_group_name']}: {m['match_percentage']}%")
            
    if "aspiration_matches" in result and result["aspiration_matches"]:
        print("\n  [Aspiration Matches]:")
        for a in result["aspiration_matches"]:
            print(f"   -> {a.get('major_name')} ({a.get('major_group_name')}): {a.get('match_percentage')}%")
            
    print("\n  [Program Recommendations]:")
    recs = result.get("recommendations", [])
    if not recs:
        print("   (No recommendations found)")
        return
        
    for r in recs:
        safety = r.get("safety_level", "unknown")
        trend = r.get("score_trend", "unknown")
        score = r.get("latest_score_thpt", "N/A")
        print(f"   [{safety.upper()}] {r.get('university_code')} - {r.get('major_name')}")
        print(f"        Score: {score} | Trend: {trend} | Rec Score: {r.get('recommendation_score')}")

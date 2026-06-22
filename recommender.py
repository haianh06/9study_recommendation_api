"""
Recommendation Engine
======================
Career & University Recommendation System

3-Stage Pipeline:
  Stage 1: Rule-Based Hard Filtering (Knowledge-Based)
  Stage 2: Content-Based Similarity Scoring
  Stage 3: Knowledge-Based Re-ranking & Blended Recommendation (Aspiration vs Discovery)

Input: User profile dict
Output: Ranked list of (program, score, explanations) + Top Majors Match
"""

import numpy as np
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from personality_mapper import HOLLAND_MAP, NUMEROLOGY_MAP


@dataclass
class UserProfile:
    """Represents a user's input profile for recommendation."""
    
    # Level 1 (Required)
    exam_block: List[str]             # e.g., ["A00", "A01", "D01"]
    total_score: float                # Tổng điểm (thang 30)
    province: str                     # Tỉnh/TP hiện tại
    
    # Aspirations & Personality (Blended Recommendation)
    aspirations: List[Dict[str, str]] = field(default_factory=list) # e.g. [{"university_code": "BKA", "major_name": "Công nghệ thông tin"}]
    holland_code: Optional[str] = None
    numerology: Optional[int] = None
    
    # Level 2 (Recommended)
    subject_scores: Dict[str, float] = field(default_factory=dict)   # {"Toán": 8.5, "Lý": 7.0}
    budget_max: Optional[float] = None          # VND/năm
    program_type: Optional[str] = None          # "Đại trà", "Chất lượng cao", etc.
    preferred_provinces: List[str] = field(default_factory=list)     # Tỉnh/TP muốn học
    university_type: Optional[str] = None       # "Công lập", "Dân lập"
    
    # Level 3 (Optional)
    interest_keywords: List[str] = field(default_factory=list)       # ["công nghệ", "kinh doanh"]
    major_group_ids: List[str] = field(default_factory=list)         # Top nhóm ngành yêu thích
    major_group_names: List[str] = field(default_factory=list)       # Tên nhóm ngành


class RecommendationEngine:
    """
    3-Stage recommendation pipeline:
    1. Hard Filter → remove infeasible programs
    2. Score → compute match scores
    3. Re-rank → apply diversity/safety balancing
    """

    # Default weights for scoring (expert-defined, tunable)
    DEFAULT_WEIGHTS = {
        "score_match": 0.30,       # How well user's score matches admission score
        "location_match": 0.15,    # Geographic preference
        "interest_match": 0.20,    # Major group / keyword match
        "budget_match": 0.10,      # Tuition affordability
        "quota_factor": 0.05,      # Higher quota = easier admission
        "prestige_score": 0.10,    # University popularity/prestige proxy
        "trend_bonus": 0.10,       # Score trend (stable/down = slightly easier)
    }

    def __init__(self, catalog: pd.DataFrame, weights: Optional[Dict[str, float]] = None):
        """
        Args:
            catalog: Program catalog DataFrame from DataLoader.build_program_catalog()
            weights: Optional custom weights for scoring factors
        """
        self.catalog = catalog.copy()
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._preprocess_catalog()

    def _preprocess_catalog(self):
        """Pre-compute values needed for scoring."""
        # Normalize tuition for scoring
        tuition_vals = self.catalog["tuition_min"].dropna()
        if len(tuition_vals) > 0:
            self._tuition_median = tuition_vals.median()
            self._tuition_max = tuition_vals.max()
        else:
            self._tuition_median = 20_000_000
            self._tuition_max = 100_000_000

        # Normalize quota
        quota_vals = self.catalog["total_quota"].dropna()
        if len(quota_vals) > 0:
            self._quota_median = quota_vals.median()
            self._quota_max = quota_vals.max()
        else:
            self._quota_median = 50
            self._quota_max = 500

        # Pre-compute text features for interest matching
        self.catalog["_search_text"] = (
            self.catalog["major_name"].fillna("").str.lower() + " " +
            self.catalog["specialization"].fillna("").str.lower() + " " +
            self.catalog["major_group_name"].fillna("").str.lower()
        )

    # ═══════════════════════════════════════════════════════
    # DYNAMIC MAJOR MATCH PERCENTAGE (UI Layer)
    # ═══════════════════════════════════════════════════════

    def _calculate_major_match_percent(self, user: UserProfile, group_name: str) -> float:
        """
        Calculate dynamic match percentage for a major group
        based on Holland (50%), Numerology (30%), Explicit Interest (20%).
        """
        has_holland = bool(user.holland_code)
        has_num = bool(user.numerology)
        
        holland_score = 0.0
        num_score = 0.0
        interest_score = 0.0
        
        # Holland Match
        if has_holland:
            codes = user.holland_code.upper()[:3]
            for i, c in enumerate(codes):
                if c in HOLLAND_MAP and group_name in HOLLAND_MAP[c]["major_groups"]:
                    # Primary letter = 1.0, secondary = 0.8, tertiary = 0.6
                    holland_score = max(holland_score, 1.0 - (i * 0.2))
                    
        # Numerology Match
        if has_num:
            if user.numerology in NUMEROLOGY_MAP and group_name in NUMEROLOGY_MAP[user.numerology]:
                num_score = 1.0
                
        # Interest Match (Explicit)
        if group_name in user.major_group_names:
            interest_score = 1.0
            
        # Check Aspirations
        for asp in user.aspirations:
            if asp.get("major_name") and str(asp.get("major_name")).lower() in group_name.lower():
                interest_score = 1.0
            
        # Dynamic Weighting
        if has_holland:
            final_score = (holland_score * 0.5) + (num_score * 0.3) + (interest_score * 0.2)
        elif has_num:
            final_score = (num_score * 0.5) + (interest_score * 0.5)
        else:
            final_score = interest_score
            
        return min(final_score, 1.0)

    # ═══════════════════════════════════════════════════════
    # STAGE 1: Hard Filtering
    # ═══════════════════════════════════════════════════════

    def _hard_filter(self, user: UserProfile, score_margin: float = 3.0) -> pd.DataFrame:
        """Remove programs that are clearly infeasible."""
        df = self.catalog.copy()
        initial_count = len(df)
        filter_log = []

        # Filter 1: Exam block compatibility
        if user.exam_block:
            def has_matching_block(exam_blocks_list):
                if not exam_blocks_list or not isinstance(exam_blocks_list, list):
                    return True  # If no block info, keep it
                if len(exam_blocks_list) == 0:
                    return True
                for block in exam_blocks_list:
                    if isinstance(block, str) and block in user.exam_block:
                        return True
                    elif isinstance(block, dict) and block.get("code") in user.exam_block:
                        return True
                return False
            
            mask = df["exam_blocks_list"].apply(has_matching_block)
            df = df[mask]
            filter_log.append(f"Exam block filter: {initial_count} → {len(df)}")

        # Filter 2: Score feasibility (margin applied later for reach)
        # We allow up to 3 points difference for "Reach" category
        has_score_mask = df["latest_score_thpt"].notna()
        score_feasible = (
            ~has_score_mask |
            (df["latest_score_thpt"] <= user.total_score + score_margin)
        )
        df = df[score_feasible]
        filter_log.append(f"Score feasibility filter (margin={score_margin}): → {len(df)}")

        return df, filter_log

    # ═══════════════════════════════════════════════════════
    # STAGE 2: Scoring Functions
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _score_match(user_score: float, program_score: Optional[float], sigma: float = 3.0) -> float:
        if program_score is None or np.isnan(program_score):
            return 0.4
        diff = user_score - program_score
        base = np.exp(-0.5 * (diff / sigma) ** 2)
        if diff > 0:
            safety_bonus = min(0.15, diff * 0.03)
            return min(1.0, base + safety_bonus)
        else:
            return base * 0.9

    @staticmethod
    def _location_match(user_province: str, uni_province: Optional[str],
                         preferred_provinces: List[str]) -> float:
        if uni_province is None or (isinstance(uni_province, float) and np.isnan(uni_province)):
            return 0.3
        uni_prov_lower = str(uni_province).lower().strip()
        user_prov_lower = user_province.lower().strip()
        
        if uni_prov_lower == user_prov_lower:
            return 1.0
        for pref in preferred_provinces:
            if pref.lower().strip() == uni_prov_lower:
                return 0.75
        major_cities = ["hà nội", "tp.hcm", "đà nẵng", "hải phòng", "cần thơ"]
        if uni_prov_lower in major_cities:
            return 0.4
        return 0.2

    @staticmethod
    def _budget_match(user_budget_max: Optional[float], tuition_min: Optional[float]) -> float:
        if user_budget_max is None:
            return 0.7
        if tuition_min is None or np.isnan(tuition_min):
            return 0.5
        if tuition_min <= 0:
            return 0.7
        if tuition_min <= user_budget_max:
            return 1.0
        else:
            over_ratio = (tuition_min - user_budget_max) / user_budget_max
            return max(0.0, 1.0 - over_ratio * 2)

    def _interest_match(self, user: UserProfile, search_text: str, major_group_name: Optional[str]) -> float:
        score = 0.0
        count = 0
        if user.major_group_names and major_group_name:
            if major_group_name in user.major_group_names:
                score += 1.0
            else:
                score += 0.2
            count += 1
        if user.interest_keywords and search_text:
            keyword_hits = sum(1 for kw in user.interest_keywords if kw.lower() in search_text)
            if len(user.interest_keywords) > 0:
                score += keyword_hits / len(user.interest_keywords)
                count += 1
        return score / count if count > 0 else 0.5

    def _quota_factor(self, total_quota: Optional[float]) -> float:
        if total_quota is None or np.isnan(total_quota) or total_quota <= 0:
            return 0.5
        ratio = min(total_quota / self._quota_max, 1.0)
        return 0.3 + 0.5 * ratio

    def _prestige_score(self, row: pd.Series) -> float:
        score = 0.5
        if row.get("is_featured"): score += 0.2
        if pd.notna(row.get("official_link")): score += 0.1
        latest_score = row.get("latest_score_thpt")
        if pd.notna(latest_score) and latest_score > 20: score += 0.15
        return min(1.0, score)

    @staticmethod
    def _trend_bonus(trend: Optional[str]) -> float:
        if trend == "down": return 0.7
        elif trend == "stable": return 0.6
        elif trend == "up": return 0.4
        return 0.5

    def _compute_scores(self, user: UserProfile, filtered_df: pd.DataFrame) -> pd.DataFrame:
        df = filtered_df.copy()
        w = self.weights

        df["_score_match"] = df["latest_score_thpt"].apply(lambda x: self._score_match(user.total_score, x))
        df["_location_match"] = df.apply(lambda row: self._location_match(user.province, row.get("province"), user.preferred_provinces), axis=1)
        df["_budget_match"] = df["tuition_min"].apply(lambda x: self._budget_match(user.budget_max, x))
        df["_interest_match"] = df.apply(lambda row: self._interest_match(user, row.get("_search_text", ""), row.get("major_group_name")), axis=1)
        df["_quota_factor"] = df["total_quota"].apply(self._quota_factor)
        df["_prestige_score"] = df.apply(self._prestige_score, axis=1)
        df["_trend_bonus"] = df["score_trend"].apply(self._trend_bonus)

        df["recommendation_score"] = (
            w["score_match"]    * df["_score_match"] +
            w["location_match"] * df["_location_match"] +
            w["interest_match"] * df["_interest_match"] +
            w["budget_match"]   * df["_budget_match"] +
            w["quota_factor"]   * df["_quota_factor"] +
            w["prestige_score"] * df["_prestige_score"] +
            w["trend_bonus"]    * df["_trend_bonus"]
        )

        return df

    # ═══════════════════════════════════════════════════════
    # STAGE 3: Re-ranking & Safety Classification
    # ═══════════════════════════════════════════════════════

    def _rerank(self, scored_df: pd.DataFrame, user: UserProfile, top_k: int = 20) -> pd.DataFrame:
        df = scored_df.sort_values(["is_aspiration", "recommendation_score"], ascending=[False, False]).copy()

        def classify_safety(row):
            score = row.get("latest_score_thpt")
            if pd.isna(score): return "unknown"
            diff = user.total_score - score
            if diff >= 1: return "safe"           # An toàn (User >= Điểm chuẩn + 1)
            elif diff >= -1: return "match"       # Vừa sức (User +- 1)
            elif diff >= -3: return "reach"       # Thử thách (User -3 -> -1)
            else: return "ambitious"

        df["safety_level"] = df.apply(classify_safety, axis=1)

        selected = []
        seen_universities = set()
        seen_major_groups = set()
        
        candidates = df.to_dict("records")
        for candidate in candidates:
            # Aspirations bypass diversity constraints
            if not candidate.get("is_aspiration"):
                if len(selected) >= top_k:
                    break
                
                uni_id = candidate.get("university_id")
                group_name = candidate.get("major_group_name")
                
                if sum(1 for s in selected if s.get("university_id") == uni_id and not s.get("is_aspiration")) >= 3:
                    continue
                if sum(1 for s in selected if s.get("major_group_name") == group_name and not s.get("is_aspiration")) >= 5:
                    continue
                
                seen_universities.add(uni_id)
                seen_major_groups.add(group_name)
            
            selected.append(candidate)

        return pd.DataFrame(selected)

    # ═══════════════════════════════════════════════════════
    # Main API
    # ═══════════════════════════════════════════════════════

    def recommend(self, user: UserProfile, top_k: int = 20, 
                  score_margin: float = 3.0,
                  return_explanations: bool = True) -> Dict[str, Any]:
        """
        Main recommendation function with Blended output.
        """
        # 1. Compute Top Majors Match Percentages
        top_majors = []
        all_groups = self.catalog["major_group_name"].dropna().unique()
        for g in all_groups:
            score = self._calculate_major_match_percent(user, g)
            if score > 0:
                top_majors.append({
                    "major_group_name": g, 
                    "match_percentage": round(score * 100)
                })
        
        # Sort and take top 10
        top_majors = sorted(top_majors, key=lambda x: x["match_percentage"], reverse=True)[:10]

        # 2. Enrich User Profile with Discovery Interests
        # We temporarily boost the interest_match for majors the system found compatible
        original_interest = user.major_group_names.copy()
        extended_interest = set(original_interest)
        for tm in top_majors:
            if tm["match_percentage"] >= 60:
                extended_interest.add(tm["major_group_name"])
        user.major_group_names = list(extended_interest)

        # 3. Filter & Score
        filtered_df, filter_log = self._hard_filter(user, score_margin)
        
        if len(filtered_df) == 0:
            user.major_group_names = original_interest
            return {
                "top_majors": top_majors,
                "recommendations": [],
                "metadata": {"after_filter": 0, "message": "No programs match your criteria."}
            }

        scored_df = self._compute_scores(user, filtered_df)

        # 4. Mark Aspirations
        if len(user.aspirations) > 0:
            def is_aspiration(row):
                for asp in user.aspirations:
                    match_uni = not asp.get("university_code") or str(row.get("university_code")).lower() == asp.get("university_code").lower()
                    match_major = not asp.get("major_name") or (
                        asp.get("major_name").lower() in str(row.get("major_name", "")).lower() or
                        asp.get("major_name").lower() in str(row.get("major_group_name", "")).lower()
                    )
                    if match_uni and match_major:
                        return True
                return False
            scored_df["is_aspiration"] = scored_df.apply(is_aspiration, axis=1)
        else:
            scored_df["is_aspiration"] = False

        # 5. Fallback logic for Aspirations
        # If user has an aspiration that is too hard (or didn't even pass score filter)
        # The frontend can use `is_aspiration=False` results as "Có thể cân nhắc"
        
        # Restore original interest
        user.major_group_names = original_interest

        # 6. Re-rank
        final_df = self._rerank(scored_df, user, top_k)

        # Build output
        output_columns = [
            "program_id", "university_code", "university_name", "province",
            "major_code", "major_name", "major_group_name", "program_type",
            "tuition_min", "latest_score_thpt", "score_trend",
            "safety_level", "recommendation_score", "is_aspiration"
        ]
        
        available_cols = [c for c in output_columns if c in final_df.columns]
        recommendations = final_df[available_cols].to_dict("records")

        # Cleanup numeric outputs
        for rec in recommendations:
            if "recommendation_score" in rec:
                rec["recommendation_score"] = round(rec["recommendation_score"], 4)
            if "latest_score_thpt" in rec and pd.notna(rec["latest_score_thpt"]):
                rec["latest_score_thpt"] = round(float(rec["latest_score_thpt"]), 2)
            else:
                rec["latest_score_thpt"] = None
            if "tuition_min" in rec and pd.isna(rec["tuition_min"]):
                rec["tuition_min"] = None

        metadata = {
            "total_programs": len(self.catalog),
            "after_filter": len(filtered_df),
            "returned": len(recommendations),
            "safety_distribution": final_df["safety_level"].value_counts().to_dict() if "safety_level" in final_df.columns else {},
        }

        return {
            "top_majors": top_majors,
            "recommendations": recommendations,
            "metadata": metadata,
        }

"""
Data Loader & Preprocessor Module
===================================
Career & University Recommendation System

Loads and preprocesses data from the 9study PostgreSQL database.
All operations are READ-ONLY.
"""

import os
import json
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from typing import Dict, List, Optional, Tuple

load_dotenv(override=True)


class DataLoader:
    """Handles all database reads and preprocessing for the recommendation engine."""

    # Score type classification by admission method
    # Different methods use different score scales
    SCORE_SCALE_MAP = {
        # Thang 30 (3 môn × 10 điểm) — thi THPT
        "thpt": {"min": 0, "max": 30, "label": "THPT QG (thang 30)"},
        "hoc_ba": {"min": 0, "max": 30, "label": "Học bạ (thang 30)"},
        # Thang 40 (4 môn hoặc có điểm ưu tiên)
        "dgnl": {"min": 0, "max": 1200, "label": "ĐGNL (thang 1200)"},
        "dgtd": {"min": 0, "max": 100, "label": "ĐGTD (thang 100)"},
        # Thang 100 — các kỳ thi năng lực
        "ccqt": {"min": 0, "max": 3000, "label": "Chứng chỉ quốc tế"},
        "xthb": {"min": 0, "max": 30, "label": "Xét tuyển học bạ (thang 30)"},
        "xt_hb": {"min": 0, "max": 30, "label": "XT Học bạ (thang 30)"},
    }

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL not found. Set it in .env or pass directly.")
        self.engine = create_engine(self.database_url, echo=False)
        self._cache: Dict[str, pd.DataFrame] = {}

    def _read_sql_cached(self, query: str, cache_key: str) -> pd.DataFrame:
        """Read SQL with simple in-memory caching."""
        if cache_key not in self._cache:
            self._cache[cache_key] = pd.read_sql(query, self.engine)
        return self._cache[cache_key].copy()

    # ──────────────────────────────────────────────
    # Core Data Loading
    # ──────────────────────────────────────────────

    def load_universities(self) -> pd.DataFrame:
        """Load all active universities with key metadata."""
        return self._read_sql_cached("""
            SELECT id, university_code, name, short_name, province, type,
                   website, logo_url, featured_major, overview_text,
                   facts, tuition_status, tuition_text,
                   campus_count, credits_per_year
            FROM universities 
            WHERE deleted_at IS NULL
        """, "universities")

    def load_programs(self) -> pd.DataFrame:
        """Load all active programs with university info."""
        return self._read_sql_cached("""
            SELECT p.id, p.university_id, p.major_code, p.major_name,
                   p.program_type, p.specialization, p.major_group_id,
                   p.total_quota, p.tuition_min, p.tuition_max,
                   p.is_featured, p.official_link,
                   u.university_code, u.name as university_name,
                   u.province, u.type as university_type
            FROM programs p
            JOIN universities u ON p.university_id = u.id
            WHERE p.deleted_at IS NULL AND u.deleted_at IS NULL
        """, "programs")

    def load_major_groups(self) -> pd.DataFrame:
        """Load major group reference data."""
        return self._read_sql_cached(
            "SELECT id, name, icon FROM major_groups",
            "major_groups"
        )

    def load_admission_scores(self) -> pd.DataFrame:
        """Load admission scores with full context (program + university)."""
        return self._read_sql_cached("""
            SELECT 
                a_s.id as score_id, a_s.year, a_s.score, a_s.note,
                pa.id as program_admission_id, pa.program_id, 
                pa.method, pa.exam_blocks,
                p.major_code, p.major_name, p.major_group_id,
                p.program_type, p.specialization,
                p.total_quota, p.tuition_min, p.tuition_max,
                u.id as university_id, u.university_code, 
                u.name as university_name, u.province, u.type as university_type
            FROM admission_scores a_s
            JOIN program_admissions pa ON a_s.program_admission_id = pa.id
            JOIN programs p ON pa.program_id = p.id
            JOIN universities u ON p.university_id = u.id
            WHERE a_s.deleted_at IS NULL 
              AND pa.deleted_at IS NULL
              AND p.deleted_at IS NULL
              AND u.deleted_at IS NULL
        """, "admission_scores")

    def load_program_admissions(self) -> pd.DataFrame:
        """Load program admission methods (which methods each program accepts)."""
        return self._read_sql_cached("""
            SELECT pa.id, pa.program_id, pa.method, pa.exam_blocks
            FROM program_admissions pa
            JOIN programs p ON pa.program_id = p.id
            WHERE pa.deleted_at IS NULL AND p.deleted_at IS NULL
        """, "program_admissions")

    def load_subjects(self) -> pd.DataFrame:
        """Load subject reference data."""
        return self._read_sql_cached(
            "SELECT id, name, short_name FROM subjects WHERE deleted_at IS NULL ORDER BY sort_order",
            "subjects"
        )

    # ──────────────────────────────────────────────
    # Preprocessing
    # ──────────────────────────────────────────────

    def build_program_catalog(self) -> pd.DataFrame:
        """
        Build the complete program catalog with all features needed for recommendation.
        This is the main 'Item' dataset.
        
        Returns DataFrame with columns:
        - program_id, university_id, university_code, university_name
        - major_code, major_name, major_group_id, major_group_name
        - province, university_type, program_type, specialization
        - tuition_min, tuition_max, total_quota
        - latest_score_thpt (latest THPT score for the program)
        - score_trend (up/down/stable based on recent years)
        - admission_methods (list of accepted methods)
        - exam_blocks_list (list of accepted exam blocks)
        """
        programs = self.load_programs()
        major_groups = self.load_major_groups()
        scores = self.load_admission_scores()
        admissions = self.load_program_admissions()

        # Merge major group names
        catalog = programs.merge(
            major_groups.rename(columns={"id": "mg_id", "name": "major_group_name"}),
            left_on="major_group_id",
            right_on="mg_id",
            how="left"
        ).drop(columns=["mg_id"], errors="ignore")

        # ── Compute latest THPT score per program ──
        thpt_scores = scores[
            (scores["method"].isin(["thpt", "hoc_ba", "xthb", "xt_hb"])) &
            (scores["score"].notna()) &
            (scores["score"] > 0) &
            (scores["score"] <= 30) &
            (scores["year"] >= 2020)
        ].copy()

        if len(thpt_scores) > 0:
            # Latest year score per program
            latest_year = thpt_scores.groupby("program_id")["year"].max().reset_index()
            latest_year.columns = ["program_id", "latest_year"]

            latest_scores = thpt_scores.merge(
                latest_year, 
                left_on=["program_id", "year"],
                right_on=["program_id", "latest_year"]
            )
            # Take median if multiple scores for same program/year
            latest_score_agg = latest_scores.groupby("program_id").agg(
                latest_score_thpt=("score", "median"),
                latest_score_year=("latest_year", "first")
            ).reset_index()

            catalog = catalog.merge(latest_score_agg, left_on="id", right_on="program_id",
                                     how="left", suffixes=("", "_score"))
            catalog.drop(columns=["program_id_score"], errors="ignore", inplace=True)
        else:
            catalog["latest_score_thpt"] = np.nan
            catalog["latest_score_year"] = np.nan

        # ── Compute score trend ──
        if len(thpt_scores) > 0:
            yearly = thpt_scores.groupby(["program_id", "year"])["score"].median().reset_index()
            
            def compute_trend(group):
                if len(group) < 2:
                    return "unknown"
                group = group.sort_values("year")
                recent = group.tail(3)
                if len(recent) < 2:
                    return "unknown"
                diff = recent["score"].iloc[-1] - recent["score"].iloc[0]
                if diff > 1.0:
                    return "up"
                elif diff < -1.0:
                    return "down"
                else:
                    return "stable"
            
            trends = yearly.groupby("program_id").apply(compute_trend, include_groups=False).reset_index()
            trends.columns = ["program_id", "score_trend"]
            catalog = catalog.merge(trends, left_on="id", right_on="program_id",
                                     how="left", suffixes=("", "_trend"))
            catalog.drop(columns=["program_id_trend"], errors="ignore", inplace=True)
        else:
            catalog["score_trend"] = "unknown"

        # ── Aggregate admission methods and exam blocks per program ──
        method_agg = admissions.groupby("program_id").agg(
            admission_methods=("method", lambda x: list(set(x.dropna()))),
            exam_blocks_raw=("exam_blocks", "first")
        ).reset_index()
        
        catalog = catalog.merge(method_agg, left_on="id", right_on="program_id",
                                 how="left", suffixes=("", "_adm"))
        catalog.drop(columns=["program_id_adm"], errors="ignore", inplace=True)

        # Parse exam_blocks from JSONB
        def parse_exam_blocks(raw):
            if raw is None:
                return []
            if isinstance(raw, list):
                return raw
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return []
            return []

        catalog["exam_blocks_list"] = catalog["exam_blocks_raw"].apply(parse_exam_blocks)
        catalog.drop(columns=["exam_blocks_raw"], errors="ignore", inplace=True)

        # Rename id to program_id for clarity
        catalog = catalog.rename(columns={"id": "program_id"})

        return catalog

    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    
    loader = DataLoader()
    
    print("Loading program catalog...")
    catalog = loader.build_program_catalog()
    
    print(f"\n{'='*60}")
    print(f"PROGRAM CATALOG SUMMARY")
    print(f"{'='*60}")
    print(f"Total programs  : {len(catalog):,}")
    print(f"Columns         : {catalog.columns.tolist()}")
    print(f"\nMissing values:")
    missing = catalog.isnull().sum()
    for col, cnt in missing[missing > 0].items():
        print(f"  {col}: {cnt} ({cnt/len(catalog)*100:.1f}%)")
    
    print(f"\nScore coverage:")
    has_score = catalog["latest_score_thpt"].notna().sum()
    print(f"  Programs with THPT score: {has_score} ({has_score/len(catalog)*100:.1f}%)")
    
    print(f"\nScore trend distribution:")
    if "score_trend" in catalog.columns:
        print(catalog["score_trend"].value_counts().to_string())
    
    print(f"\nSample rows:")
    print(catalog[["program_id", "university_code", "major_name", "major_group_name", 
                    "province", "latest_score_thpt", "score_trend"]].head(10).to_string())

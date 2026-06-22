"""
FastAPI Endpoint — Career & University Recommendation System
=============================================================
Provides REST API for the recommendation engine.

Usage:
    uvicorn api:app --reload --port 8000

Endpoints:
    POST /recommend     → Get recommendations for a user profile
    GET  /major-groups  → List all available major groups
    GET  /health        → Health check
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from data_loader import DataLoader
from recommender import RecommendationEngine, UserProfile
from personality_mapper import get_recommendations_from_mbti, get_recommendations_from_holland


# ──────────────────────────────────────────
# Pydantic Models (Request/Response)
# ──────────────────────────────────────────

class AspirationInput(BaseModel):
    university_code: Optional[str] = None
    major_name: Optional[str] = None


class RecommendationRequest(BaseModel):
    """User profile input for recommendations."""
    # Level 1 (Required)
    exam_block: List[str] = Field(..., description="Khối thi, e.g. ['A00', 'A01']")
    total_score: float = Field(..., ge=0, le=30, description="Tổng điểm (thang 30)")
    province: str = Field(..., description="Tỉnh/TP hiện tại")
    
    # Level 2 (Optional)
    subject_scores: Dict[str, float] = Field(default_factory=dict, description="Điểm từng môn")
    budget_max: Optional[float] = Field(None, ge=0, description="Ngân sách tối đa (VND/năm)")
    program_type: Optional[str] = Field(None, description="Loại chương trình: 'Đại trà', 'Chất lượng cao'")
    preferred_provinces: List[str] = Field(default_factory=list, description="Tỉnh/TP ưu tiên học")
    university_type: Optional[str] = Field(None, description="'Công lập' hoặc 'Dân lập'")
    
    # Level 3 (Optional)
    interest_keywords: List[str] = Field(default_factory=list, description="Từ khóa sở thích")
    major_group_names: List[str] = Field(default_factory=list, description="Tên nhóm ngành yêu thích")
    
    # Aspirations & Personality
    aspirations: List[AspirationInput] = Field(default_factory=list, description="Các nguyện vọng (Trường/Ngành)")
    holland_code: Optional[str] = Field(None, description="Mã Holland (e.g. RIA)")
    numerology: Optional[int] = Field(None, description="Số chủ đạo Thần số học (e.g. 22)")
    
    # Settings
    top_k: int = Field(20, ge=1, le=50, description="Số lượng kết quả")
    score_margin: float = Field(3.0, ge=0, le=10, description="Biên điểm cho phép (điểm)")

    class Config:
        json_schema_extra = {
            "example": {
                "exam_block": ["A00"],
                "total_score": 24.5,
                "province": "Hà Nội",
                "preferred_provinces": ["Hà Nội", "TP.HCM"],
                "interest_keywords": ["công nghệ", "phần mềm"],
                "major_group_names": ["Khoa học máy tính - Kỹ thuật phần mềm"],
                "top_k": 10,
                "score_margin": 3.0
            }
        }


class ProgramRecommendation(BaseModel):
    """A single program recommendation."""
    program_id: Optional[str] = None
    university_code: Optional[str] = None
    university_name: Optional[str] = None
    province: Optional[str] = None
    major_code: Optional[str] = None
    major_name: Optional[str] = None
    major_group_name: Optional[str] = None
    program_type: Optional[str] = None
    specialization: Optional[str] = None
    tuition_min: Optional[float] = None
    tuition_max: Optional[float] = None
    total_quota: Optional[float] = None
    latest_score_thpt: Optional[float] = None
    latest_score_year: Optional[float] = None
    score_trend: Optional[str] = None
    safety_level: Optional[str] = None
    recommendation_score: Optional[float] = None


class TopMajorResponse(BaseModel):
    major_group_name: str
    match_percentage: float


class RecommendationResponse(BaseModel):
    """Response containing recommendations and metadata."""
    top_majors: List[TopMajorResponse] = []
    recommendations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    explanations: List[Dict[str, Any]] = []


class MajorGroupResponse(BaseModel):
    """Major group info."""
    id: str
    name: str
    icon: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    catalog_size: int
    programs_with_scores: int


class PersonalityRequest(BaseModel):
    """Request for personality-based mapping."""
    mbti: Optional[str] = Field(None, description="MBTI code (e.g. INTJ)")
    holland: Optional[str] = Field(None, description="Holland RIASEC code (e.g. SEC)")


class PersonalityResponse(BaseModel):
    """Mapped major groups and keywords."""
    major_group_names: List[str]
    interest_keywords: List[str]


# ──────────────────────────────────────────
# App Initialization
# ──────────────────────────────────────────

# Global state
engine_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data on startup, cleanup on shutdown."""
    print("🔄 Loading recommendation engine...")
    
    loader = DataLoader()
    catalog = loader.build_program_catalog()
    major_groups = loader.load_major_groups()
    
    rec_engine = RecommendationEngine(catalog)
    
    engine_state["engine"] = rec_engine
    engine_state["catalog"] = catalog
    engine_state["major_groups"] = major_groups
    engine_state["loader"] = loader
    
    print(f"✅ Engine loaded: {len(catalog):,} programs")
    print(f"   {catalog['latest_score_thpt'].notna().sum():,} with THPT scores")
    
    yield
    
    print("🔌 Shutting down...")
    engine_state.clear()


app = FastAPI(
    title="9study Career & University Recommendation API",
    description="Gợi ý ngành học và trường đại học phù hợp dựa trên profile học sinh.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check system health and data status."""
    catalog = engine_state.get("catalog")
    if catalog is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    return HealthResponse(
        status="healthy",
        catalog_size=len(catalog),
        programs_with_scores=int(catalog["latest_score_thpt"].notna().sum())
    )


@app.get("/major-groups", response_model=List[MajorGroupResponse], tags=["Reference Data"])
async def list_major_groups():
    """List all available major groups (nhóm ngành)."""
    mg = engine_state.get("major_groups")
    if mg is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    return [
        MajorGroupResponse(
            id=str(row["id"]),
            name=row["name"],
            icon=row.get("icon")
        )
        for _, row in mg.iterrows()
    ]


@app.post("/onboarding/personality", response_model=PersonalityResponse, tags=["Onboarding"])
async def get_personality_mapping(request: PersonalityRequest):
    """
    Map MBTI or Holland codes to major groups and keywords for cold-start recommendations.
    """
    groups = []
    keywords = []
    
    if request.mbti:
        g, k = get_recommendations_from_mbti(request.mbti)
        groups.extend(g)
        keywords.extend(k)
        
    if request.holland:
        g, k = get_recommendations_from_holland(request.holland)
        groups.extend(g)
        keywords.extend(k)
        
    # Deduplicate
    groups = list(dict.fromkeys(groups))
    keywords = list(dict.fromkeys(keywords))
    
    return PersonalityResponse(
        major_group_names=groups,
        interest_keywords=keywords
    )


@app.post("/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_recommendations(request: RecommendationRequest):
    """
    Get personalized university & major recommendations.
    
    Input levels:
    - **Level 1 (Required)**: exam_block, total_score, province
    - **Level 2 (Recommended)**: subject_scores, budget_max, program_type, preferred_provinces
    - **Level 3 (Optional)**: interest_keywords, major_group_names
    
    The more information provided, the better the recommendations.
    """
    rec_engine = engine_state.get("engine")
    if rec_engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    # Build UserProfile from request
    user = UserProfile(
        exam_block=request.exam_block,
        total_score=request.total_score,
        province=request.province,
        subject_scores=request.subject_scores,
        budget_max=request.budget_max,
        program_type=request.program_type,
        preferred_provinces=request.preferred_provinces,
        university_type=request.university_type,
        interest_keywords=request.interest_keywords,
        major_group_names=request.major_group_names,
        aspirations=[asp.model_dump() for asp in request.aspirations],
        holland_code=request.holland_code,
        numerology=request.numerology,
    )

    # Get recommendations
    result = rec_engine.recommend(
        user,
        top_k=request.top_k,
        score_margin=request.score_margin,
        return_explanations=True
    )

    # Clean NaN values for JSON serialization
    def clean_nan(obj):
        if isinstance(obj, dict):
            return {k: clean_nan(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_nan(v) for v in obj]
        elif isinstance(obj, float) and (obj != obj):  # NaN check
            return None
        return obj

    result = clean_nan(result)

    return RecommendationResponse(**result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

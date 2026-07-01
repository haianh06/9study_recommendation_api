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
from personality_mapper import (
    get_recommendations_from_mbti, 
    get_recommendations_from_holland,
    calculate_numerology,
    get_zodiac_sign,
    HOLLAND_QUESTIONS,
    LEARNING_STYLE_QUESTIONS,
    QUIZ_SCALE,
    score_holland_answers,
    score_learning_style,
    get_personality_insights,
    get_highlight_group,
    get_numerology_insights,
)



# ──────────────────────────────────────────
# Pydantic Models (Request/Response)
# ──────────────────────────────────────────

class AspirationInput(BaseModel):
    university_code: Optional[str] = None
    major_name: Optional[str] = None


class RecommendationRequest(BaseModel):
    """User profile input for recommendations."""
    # Level 1 (Required)
    flow_type: str = Field("mock_exam", description="'mock_exam' or 'discovery'")
    exam_block: List[str] = Field(..., description="Khối thi, e.g. ['A00', 'A01']")
    total_score: float = Field(..., ge=0, le=30, description="Tổng điểm/Điểm mục tiêu (thang 30)")
    
    # Level 2 (Optional)
    current_score: Optional[float] = Field(None, ge=0, le=30, description="Điểm trung bình hiện tại (thang 30)")
    subject_scores: Dict[str, float] = Field(default_factory=dict, description="Điểm từng môn")
    program_type: Optional[str] = Field(None, description="Loại chương trình: 'Đại trà', 'Chất lượng cao'")
    university_type: Optional[str] = Field(None, description="'Công lập' hoặc 'Dân lập'")
    
    # Level 3 (Optional)
    interest_keywords: List[str] = Field(default_factory=list, description="Từ khóa sở thích")
    major_group_names: List[str] = Field(default_factory=list, description="Tên nhóm ngành yêu thích")
    
    # Aspirations & Personality
    aspirations: List[AspirationInput] = Field(default_factory=list, description="Các nguyện vọng (Trường/Ngành)")
    holland_code: Optional[str] = Field(None, description="Mã Holland (e.g. RIA)")
    dob: Optional[str] = Field(None, description="Ngày sinh (YYYY-MM-DD) để tính Thần số học và Cung hoàng đạo")
    numerology: Optional[int] = Field(None, description="Số chủ đạo Thần số học (e.g. 22)")
    
    # Settings
    top_k: int = Field(20, ge=1, le=50, description="Số lượng kết quả")
    score_margin: float = Field(3.0, ge=0, le=10, description="Biên điểm cho phép (điểm)")

    class Config:
        json_schema_extra = {
            "example": {
                "flow_type": "mock_exam",
                "exam_block": ["A00"],
                "total_score": 25.0,
                "current_score": 24.5,
                "dob": "2006-08-15",
                "aspirations": [
                    {
                        "university_code": "BKA",
                        "major_name": "Công nghệ thông tin"
                    }
                ],
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

class AspirationMatchResponse(BaseModel):
    university_code: Optional[str] = None
    major_name: Optional[str] = None
    major_group_name: str
    match_percentage: float


class TopMajorsCategorizedResponse(BaseModel):
    highly_suitable: List[TopMajorResponse] = Field(default_factory=list, description="Top majors >= 85%")
    suitable: List[TopMajorResponse] = Field(default_factory=list, description="Top majors 70% - 84%")
    need_more_info: List[TopMajorResponse] = Field(default_factory=list, description="Top majors < 70%")

class NumerologyInsightsResponse(BaseModel):
    number: int
    keywords: List[str]
    strengths: List[str]
    weaknesses: List[str]
    development: List[str]
    core_orientation: List[str]


class RecommendationResponse(BaseModel):
    """Response containing recommendations and metadata."""
    top_majors: TopMajorsCategorizedResponse
    aspiration_matches: List[AspirationMatchResponse] = []
    recommendations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    explanations: List[Dict[str, Any]] = []
    numerology_insights: Optional[NumerologyInsightsResponse] = None


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



# ── Quiz Models ──

class QuizQuestionModel(BaseModel):
    """A single quiz question."""
    id: str
    q_num: int
    text: str
    holland_group: Optional[str] = None   # only for Holland questions
    style_group: Optional[str] = None     # only for Learning Style questions


class QuizScreenModel(BaseModel):
    """One screen (màn) of quiz questions."""
    screen: int
    title: str
    description: str
    questions: List[QuizQuestionModel]


class QuizResponse(BaseModel):
    """Full quiz with all screens."""
    total_questions: int
    screens: List[QuizScreenModel]
    scale: Dict[str, Any]


class QuizAnswerRequest(BaseModel):
    """User's answers to the personality quiz."""
    answers: Dict[str, int] = Field(
        ...,
        description="Map of question_id → score (1–5). Holland IDs: H_S{screen}_Q{num}, Learning Style IDs: LS_Q{num}"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answers": {
                    "H_S1_Q1": 4, "H_S1_Q2": 3, "H_S1_Q3": 5, "H_S1_Q4": 5,
                    "H_S1_Q5": 2, "H_S1_Q6": 2, "H_S1_Q7": 3, "H_S1_Q8": 3,
                    "H_S1_Q9": 4, "H_S1_Q10": 4, "H_S1_Q11": 3, "H_S1_Q12": 3,
                    "H_S2_Q1": 4, "H_S2_Q2": 3, "H_S2_Q3": 5, "H_S2_Q4": 5,
                    "H_S2_Q5": 2, "H_S2_Q6": 2, "H_S2_Q7": 3, "H_S2_Q8": 3,
                    "H_S2_Q9": 4, "H_S2_Q10": 4, "H_S2_Q11": 3, "H_S2_Q12": 3,
                    "H_S3_Q1": 3, "H_S3_Q2": 3, "H_S3_Q3": 5, "H_S3_Q4": 5,
                    "H_S3_Q5": 2, "H_S3_Q6": 2, "H_S3_Q7": 3, "H_S3_Q8": 2,
                    "H_S3_Q9": 4, "H_S3_Q10": 4, "H_S3_Q11": 3, "H_S3_Q12": 3,
                    "LS_Q1": 3, "LS_Q2": 3, "LS_Q3": 3, "LS_Q4": 3,
                    "LS_Q5": 5, "LS_Q6": 5, "LS_Q7": 5, "LS_Q8": 5,
                    "LS_Q9": 4, "LS_Q10": 4, "LS_Q11": 3, "LS_Q12": 3,
                    "LS_Q13": 3, "LS_Q14": 3, "LS_Q15": 3, "LS_Q16": 3
                }
            }
        }


class PersonalityInsights(BaseModel):
    """Personality analysis insights (learning style focused)."""
    holland_primary: str
    holland_name: str
    holland_description: str
    holland_traits: List[str]
    suggested_careers: List[str]
    learning_style_name: str
    learning_style_description: str
    study_tips: List[str]


# ── UI-ready Holland chart models ──

class HollandGroupScore(BaseModel):
    """Một điểm trên line chart (6 nhóm theo thứ tự R-I-A-S-E-C)."""
    code: str = Field(description="Ký hiệu nhóm, e.g. 'I'")
    short_name: str = Field(description="Tên ngắn hiển thị trên chart, e.g. 'Nghiên cứu'")
    score: float = Field(description="Điểm phần trăm 0–100")


class HollandTopGroup(BaseModel):
    """Một nhóm trong footer Top 1/2/3."""
    rank: int = Field(description="Thứ hạng 1, 2 hoặc 3")
    code: str
    short_name: str
    score: float = Field(description="Điểm phần trăm 0–100")


class HollandHighlightGroup(BaseModel):
    """Dữ liệu đầy đủ cho phần 'Nhóm nổi bật nhất' trên UI."""
    code: str
    short_name: str
    full_name: str
    tagline: str
    description: str
    strengths: List[str]
    suitable_majors: List[str]
    work_environment: str


class QuizResultResponse(BaseModel):
    """
    Kết quả sau khi nộp bài test tính cách.

    Cấu trúc response map 1:1 với UI design:
    - `chart_data`      → Line chart (6 nhóm theo thứ tự R-I-A-S-E-C)
    - `highlight_group` → Phần "Nhóm nổi bật nhất" (khối màu tím giữa)
    - `top_3_groups`    → Footer Top 1 / Top 2 / Top 3
    """
    # Holland — UI ready
    holland_code: str = Field(description="Mã Holland 3 chữ cái, e.g. 'IRA'")
    chart_data: List[HollandGroupScore] = Field(description="6 nhóm theo thứ tự R-I-A-S-E-C để vẽ line chart")
    highlight_group: HollandHighlightGroup = Field(description="Nhóm #1 với mô tả đầy đủ")
    top_3_groups: List[HollandTopGroup] = Field(description="Top 3 nhóm cao điểm nhất")
    # Holland — raw data
    holland_scores: Dict[str, int] = Field(description="Điểm thô mỗi nhóm (tối đa 30)")
    holland_percentages: Dict[str, float] = Field(description="Phần trăm mỗi nhóm (0–100)")
    # Learning Style
    learning_style: str = Field(description="Phong cách học nổi trội")
    learning_style_scores: Dict[str, int]
    learning_style_percentages: Dict[str, float]
    # Recommendations
    major_group_names: List[str] = Field(description="Nhóm ngành gợi ý dựa trên Holland code")
    interest_keywords: List[str]
    # Insights
    personality_insights: PersonalityInsights


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


@app.get("/onboarding/quiz", response_model=QuizResponse, tags=["Onboarding"])
async def get_onboarding_quiz():
    """
    Lấy toàn bộ bộ câu hỏi onboarding (52 câu, 4 màn).

    **Cấu trúc:**
    - Màn 1 – "Tôi là người…" (12 câu Holland, nhóm tính cách)
    - Màn 2 – "Tôi có thể…" (12 câu Holland, nhóm năng lực)
    - Màn 3 – "Tôi thích…" (12 câu Holland, nhóm sở thích)
    - Màn 4 – Phong cách học tập (16 câu Learning Style)

    **Thang điểm:** 1 (Rất không giống) → 5 (Rất giống)

    Sau khi thu thập đủ câu trả lời, gọi `POST /onboarding/quiz/submit`.
    """
    screen_meta = [
        {
            "screen": 1,
            "title": "Tôi là người…",
            "description": "Đánh giá mức độ phù hợp với từng mô tả về tính cách của bạn."
        },
        {
            "screen": 2,
            "title": "Tôi có thể…",
            "description": "Đánh giá mức độ bạn có thể thực hiện những việc sau."
        },
        {
            "screen": 3,
            "title": "Tôi thích…",
            "description": "Đánh giá mức độ bạn yêu thích các hoạt động sau."
        },
        {
            "screen": 4,
            "title": "Phong cách học tập",
            "description": "Đánh giá mức độ phù hợp với cách bạn thường học."
        },
    ]

    screens = []

    # Màn 1–3: Holland RIASEC
    for meta in screen_meta[:3]:
        s = meta["screen"]
        q_list = [
            QuizQuestionModel(
                id=q["id"],
                q_num=q["q_num"],
                text=q["text"],
                holland_group=q["holland_group"]
            )
            for q in HOLLAND_QUESTIONS if q["screen"] == s
        ]
        screens.append(QuizScreenModel(
            screen=s,
            title=meta["title"],
            description=meta["description"],
            questions=q_list
        ))

    # Màn 4: Learning Style
    ls_questions = [
        QuizQuestionModel(
            id=q["id"],
            q_num=q["q_num"],
            text=q["text"],
            style_group=q["style_group"]
        )
        for q in LEARNING_STYLE_QUESTIONS
    ]
    screens.append(QuizScreenModel(
        screen=4,
        title=screen_meta[3]["title"],
        description=screen_meta[3]["description"],
        questions=ls_questions
    ))

    total = sum(len(sc.questions) for sc in screens)

    return QuizResponse(
        total_questions=total,
        screens=screens,
        scale=QUIZ_SCALE
    )


@app.post("/onboarding/quiz/submit", response_model=QuizResultResponse, tags=["Onboarding"])
async def submit_onboarding_quiz(request: QuizAnswerRequest):
    """
    Nộp câu trả lời bộ test tính cách và nhận kết quả phân tích.

    **Input:** dict `answers` với key = question_id, value = điểm 1–5.
    - Holland IDs: `H_S{screen}_Q{num}` (36 câu, màn 1–3)
    - Learning Style IDs: `LS_Q{num}` (16 câu, màn 4)

    **Output:**
    - `holland_code`: Mã Holland 3 chữ cái (ví dụ: "RIA")
    - `learning_style`: Phong cách học tập nổi trội
    - `major_group_names`: Nhóm ngành được gợi ý
    - `personality_insights`: Phân tích chi tiết và tips học tập
    """
    answers = request.answers

    # Validate: cần ít nhất 1 câu Holland hoặc Learning Style
    holland_ans = {k: v for k, v in answers.items() if k.startswith("H_")}
    ls_ans = {k: v for k, v in answers.items() if k.startswith("LS_")}

    if not holland_ans and not ls_ans:
        raise HTTPException(
            status_code=422,
            detail="Cần cung cấp ít nhất 1 câu trả lời (Holland: H_S*_Q* hoặc Learning Style: LS_Q*)"
        )

    # Score Holland
    holland_result = score_holland_answers(holland_ans)
    holland_code = holland_result["holland_code"]

    # Score Learning Style
    ls_result = score_learning_style(ls_ans)
    dominant_style = ls_result["dominant_style"]

    # Map Holland code → major groups + keywords
    major_groups, keywords = get_recommendations_from_holland(holland_code)

    # Build UI-ready chart data
    chart_data = [HollandGroupScore(**item) for item in holland_result["chart_data"]]
    top_3_groups = [HollandTopGroup(**item) for item in holland_result["top_3_groups"]]
    highlight_raw = get_highlight_group(holland_code)
    highlight = HollandHighlightGroup(**highlight_raw)

    # Build personality insights (learning style focused)
    insights_raw = get_personality_insights(holland_code, dominant_style)
    insights = PersonalityInsights(**insights_raw)

    return QuizResultResponse(
        # Holland — UI ready
        holland_code=holland_code,
        chart_data=chart_data,
        highlight_group=highlight,
        top_3_groups=top_3_groups,
        # Holland — raw
        holland_scores=holland_result["scores"],
        holland_percentages=holland_result["percentages"],
        # Learning Style
        learning_style=dominant_style,
        learning_style_scores=ls_result["scores"],
        learning_style_percentages=ls_result["percentages"],
        # Recommendations
        major_group_names=major_groups,
        interest_keywords=keywords,
        personality_insights=insights,
    )


@app.post("/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_recommendations(request: RecommendationRequest):
    """
    Get personalized university & major recommendations.
    
    Input levels:
    - **Level 1 (Required)**: exam_block, total_score
    - **Level 2 (Recommended)**: current_score, subject_scores, program_type, university_type
    - **Level 3 (Optional)**: interest_keywords, major_group_names
    
    The more information provided, the better the recommendations.
    """
    rec_engine = engine_state.get("engine")
    if rec_engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    # Process DOB to numerology and zodiac
    numerology = request.numerology
    zodiac = None
    if request.dob:
        numerology = calculate_numerology(request.dob)
        zodiac = get_zodiac_sign(request.dob)

    # Build UserProfile from request
    user = UserProfile(
        flow_type=request.flow_type,
        exam_block=request.exam_block,
        total_score=request.total_score,
        current_score=request.current_score if request.flow_type == "mock_exam" else None,
        subject_scores=request.subject_scores,
        program_type=request.program_type,
        university_type=request.university_type,
        interest_keywords=request.interest_keywords,
        major_group_names=request.major_group_names,
        aspirations=[asp.model_dump() for asp in request.aspirations],
        holland_code=request.holland_code,
        numerology=numerology,
        zodiac=zodiac,
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

    # Add numerology insights if DOB is provided
    if request.dob:
        result["numerology_insights"] = get_numerology_insights(request.dob)
    else:
        result["numerology_insights"] = None

    return RecommendationResponse(**result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

reviewer_instance = None

class ReviewRequest(BaseModel):
    code: str = Field(..., description="Code to review")
    language: str | None = Field(None, description="Programming language")
    context: str | None = Field(None, description="Additional context")
    mode: str = Field("standard", description="Review mode: quick, standard, deep")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "code": "def add(a, b):\n    return a + b",
                "language": "python",
                "context": "Simple addition function",
                "mode": "standard"
            }]
        }
    }


class DiffReviewRequest(BaseModel):
    diff: str = Field(..., description="Diff content in unified format")
    file_path: str | None = Field(None, description="File path for context")
    base_content: str | None = Field(None, description="Full file content for context")


class IssueResponse(BaseModel):
    type: str
    severity: str
    line: int
    end_line: int | None = None
    message: str
    suggestion: str | None = None
    code_suggestion: str | None = None


class SummaryResponse(BaseModel):
    total_issues: int
    bugs: int
    security_issues: int
    performance_issues: int
    style_issues: int
    quality_score: float


class ReviewResponse(BaseModel):
    status: str = "success"
    issues: list[IssueResponse]
    summary: SummaryResponse
    positive_feedback: list[str]
    file_path: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    model: str
    provider: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global reviewer_instance
    from ai_code_reviewer import CodeReviewer
    reviewer_instance = CodeReviewer()
    yield
    reviewer_instance = None


app = FastAPI(
    title="AI Code Reviewer API",
    description="Intelligent code review powered by LLMs",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "AI Code Reviewer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    from ai_code_reviewer import __version__

    return HealthResponse(
        status="healthy",
        version=__version__,
        model=reviewer_instance.config.model if reviewer_instance else "not initialized",
        provider=reviewer_instance.config.provider.value if reviewer_instance else "not initialized",
    )


@app.post("/review", response_model=ReviewResponse, tags=["Review"])
async def review_code(request: ReviewRequest):
    if not reviewer_instance:
        raise HTTPException(status_code=503, detail="Reviewer not initialized")

    try:
        from ai_code_reviewer.analyzer import ReviewMode

        if request.mode:
            reviewer_instance.config.mode = ReviewMode(request.mode)

        result = reviewer_instance.review(
            code=request.code,
            language=request.language,
            context=request.context,
        )

        return ReviewResponse(
            status="success",
            issues=[
                IssueResponse(
                    type=issue.type.value,
                    severity=issue.severity.value,
                    line=issue.line,
                    end_line=issue.end_line,
                    message=issue.message,
                    suggestion=issue.suggestion,
                    code_suggestion=issue.code_suggestion,
                )
                for issue in result.issues
            ],
            summary=SummaryResponse(
                total_issues=result.summary.total_issues,
                bugs=result.summary.bugs,
                security_issues=result.summary.security_issues,
                performance_issues=result.summary.performance_issues,
                style_issues=result.summary.style_issues,
                quality_score=result.summary.quality_score,
            ),
            positive_feedback=result.positive_feedback,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/review/diff", response_model=list[ReviewResponse], tags=["Review"])
async def review_diff(request: DiffReviewRequest):
    if not reviewer_instance:
        raise HTTPException(status_code=503, detail="Reviewer not initialized")

    try:
        base_content = None
        if request.base_content and request.file_path:
            base_content = {request.file_path: request.base_content}

        results = reviewer_instance.review_diff(
            diff=request.diff,
            base_content=base_content,
        )

        return [
            ReviewResponse(
                status="success",
                issues=[
                    IssueResponse(
                        type=issue.type.value,
                        severity=issue.severity.value,
                        line=issue.line,
                        end_line=issue.end_line,
                        message=issue.message,
                        suggestion=issue.suggestion,
                        code_suggestion=issue.code_suggestion,
                    )
                    for issue in result.issues
                ],
                summary=SummaryResponse(
                    total_issues=result.summary.total_issues,
                    bugs=result.summary.bugs,
                    security_issues=result.summary.security_issues,
                    performance_issues=result.summary.performance_issues,
                    style_issues=result.summary.style_issues,
                    quality_score=result.summary.quality_score,
                ),
                positive_feedback=result.positive_feedback,
                file_path=result.file_path,
            )
            for result in results
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/review/file", response_model=ReviewResponse, tags=["Review"])
async def review_file_content(
    file_path: str,
    content: str,
    language: str | None = None,
):
    if not reviewer_instance:
        raise HTTPException(status_code=503, detail="Reviewer not initialized")

    try:
        result = reviewer_instance.review(
            code=content,
            language=language,
            filename=file_path,
        )
        result.file_path = file_path

        return ReviewResponse(
            status="success",
            issues=[
                IssueResponse(
                    type=issue.type.value,
                    severity=issue.severity.value,
                    line=issue.line,
                    end_line=issue.end_line,
                    message=issue.message,
                    suggestion=issue.suggestion,
                    code_suggestion=issue.code_suggestion,
                )
                for issue in result.issues
            ],
            summary=SummaryResponse(
                total_issues=result.summary.total_issues,
                bugs=result.summary.bugs,
                security_issues=result.summary.security_issues,
                performance_issues=result.summary.performance_issues,
                style_issues=result.summary.style_issues,
                quality_score=result.summary.quality_score,
            ),
            positive_feedback=result.positive_feedback,
            file_path=result.file_path,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

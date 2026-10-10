from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class Category(str, Enum):
    bug = "bug"
    style = "style"
    best_practice = "best_practice"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Finding(BaseModel):
    line: int | None = Field(default=None, ge=1, description="1-based line number, if applicable")
    category: Category
    severity: Severity
    title: str = Field(max_length=200)
    explanation: str
    suggestion: str


class ReviewFeedback(BaseModel):
    """The structured JSON the GenAI model must return."""

    summary: str
    score: int = Field(ge=0, le=100, description="Overall code quality, 0-100")
    findings: list[Finding] = Field(default_factory=list)


class ReviewCreate(BaseModel):
    code: str = Field(min_length=1, max_length=settings.max_code_chars)
    language: str = Field(default="python", max_length=32)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    language: str
    code: str
    feedback: ReviewFeedback
    model: str
    created_at: datetime


class ReviewListItem(BaseModel):
    id: int
    language: str
    summary: str
    score: int
    findings_count: int
    created_at: datetime

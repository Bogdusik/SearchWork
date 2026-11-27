from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

STATUS = Literal["saved", "in_progress", "applied", "interview", "offer", "rejected"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleCallbackRequest(BaseModel):
    code: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    model_config = {"from_attributes": True}

class CVProfileOut(BaseModel):
    id: int
    skills: list[str]
    job_titles: list[str]
    keywords: list[str]
    updated_at: datetime
    model_config = {"from_attributes": True}

class JobSearchResult(BaseModel):
    """Returned by /jobs — live from internet, not persisted."""
    external_id: str
    source: str
    title: str
    company: str
    location: str
    salary_min: int | None
    salary_max: int | None
    url: str
    description: str
    match_score: int
    matched_skills: list[str] = []
    missing_skills: list[str] = []

class JobOut(BaseModel):
    """Returned inside ApplicationOut — saved to DB."""
    id: int
    external_id: str
    source: str
    title: str
    company: str
    location: str
    salary_min: int | None
    salary_max: int | None
    url: str
    description: str
    match_score: int
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class ApplicationOut(BaseModel):
    id: int
    job: JobOut
    status: str
    applied_at: datetime | None
    notes: str | None
    updated_at: datetime
    model_config = {"from_attributes": True}

class JobInput(BaseModel):
    """Job data sent from frontend when creating an application."""
    external_id: str
    source: str
    title: str
    company: str
    location: str
    salary_min: int | None = None
    salary_max: int | None = None
    url: str
    description: str
    match_score: int
    matched_skills: list[str] = []
    missing_skills: list[str] = []

class ApplicationCreate(BaseModel):
    job: JobInput
    status: STATUS = "saved"

class ApplicationUpdate(BaseModel):
    status: STATUS

class CoverLetterRequest(BaseModel):
    external_id: str
    source: str
    job_title: str
    company: str
    description: str
    force_regenerate: bool = False

class CVReviewRequest(BaseModel):
    target_role: str

class CVReviewItem(BaseModel):
    title: str
    detail: str

class PriorityItem(BaseModel):
    priority: int
    action: str
    impact: Literal["Huge", "High", "Medium", "Low"]

class CVReviewResponse(BaseModel):
    summary: str
    critical_issues: list[CVReviewItem]
    structural_issues: list[CVReviewItem]
    polish_issues: list[CVReviewItem]
    priority_table: list[PriorityItem]


class AlertSettingsIn(BaseModel):
    enabled: bool
    query: str = Field(max_length=200)
    locations: list[Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]] = Field(
        default_factory=list, max_length=10
    )
    min_score: int = Field(ge=0, le=100)
    ntfy_topic: str = Field(pattern=r"^[A-Za-z0-9_-]{8,64}$")

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be empty")
        return value

    @field_validator("locations")
    @classmethod
    def drop_blank_locations(cls, value: list[str]) -> list[str]:
        return [loc for loc in value if loc]


class AlertSettingsOut(BaseModel):
    enabled: bool
    query: str
    locations: list[str]
    min_score: int
    ntfy_topic: str
    last_scan_at: datetime | None
    model_config = ConfigDict(from_attributes=True)

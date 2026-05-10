from datetime import datetime
from typing import Literal
from pydantic import BaseModel

STATUS = Literal["saved", "applied", "interview", "offer", "rejected"]

class CVProfileOut(BaseModel):
    id: int
    skills: list[str]
    job_titles: list[str]
    keywords: list[str]
    updated_at: datetime
    model_config = {"from_attributes": True}

class JobOut(BaseModel):
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

class ApplicationCreate(BaseModel):
    job_id: int
    status: STATUS = "saved"

class ApplicationUpdate(BaseModel):
    status: STATUS

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class JDCreate(BaseModel):
    title: str
    requirements: str


class JDResponse(BaseModel):
    id: uuid.UUID
    title: str
    company: Optional[str]
    department: Optional[str]
    location: Optional[str]
    description: str
    requirements: str
    responsibilities: Optional[str]
    required_skills: Optional[list[str]]
    preferred_skills: Optional[list[str]]
    benefits: Optional[list[str]]
    employment_type: Optional[str]
    experience_level: Optional[str]
    salary_range: Optional[dict]
    is_active: bool
    embedding_generated: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FindBestCVsRequest(BaseModel):
    jd_id: uuid.UUID
    top_k: int = 10


class ContactCandidateRequest(BaseModel):
    cv_id: uuid.UUID
    jd_id: uuid.UUID

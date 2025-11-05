from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class CVResponse(BaseModel):
    id: uuid.UUID
    candidate_name: str
    email: str
    phone: Optional[str]
    raw_text: str
    summary: Optional[str]
    skills: Optional[list]
    experience: Optional[dict]
    education: Optional[dict]
    file_name: Optional[str]
    file_type: Optional[str]
    embedding_generated: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CVMatch(BaseModel):
    cv: CVResponse
    similarity_score: float

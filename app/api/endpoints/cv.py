from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.db.session import get_db
from app.models.cv import CV
from app.schemas.cv import CVResponse
from app.services.cv_processor import CVProcessor
from app.services.embedding import embedding_service
from app.core.auth import verify_secret_key

router = APIRouter()


@router.post("/upload", response_model=CVResponse, dependencies=[Depends(verify_secret_key)])
async def upload_cv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    API 1: Upload CV and add to collection
    Only accepts CV file (PDF or DOCX)
    Automatically extracts: name, email, phone, skills, summary
    Requires: X-Secret-Key header
    """
    # Extract and parse CV
    cv_data = await CVProcessor.extract_and_parse(file)

    # Validate required fields
    if not cv_data.get("email"):
        # Show first 500 chars of text for debugging
        preview = cv_data.get("raw_text", "")[:500] if cv_data.get("raw_text") else "No text extracted"
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract email from CV. Please ensure CV contains email address. Text preview: {preview}..."
        )

    if not cv_data.get("candidate_name"):
        raise HTTPException(status_code=400, detail="Could not extract name from CV. Please ensure CV contains candidate name.")

    # Check if email already exists
    result = await db.execute(select(CV).where(CV.email == cv_data["email"]))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"CV with email {cv_data['email']} already exists")

    # Create CV
    cv = CV(
        candidate_name=cv_data["candidate_name"],
        email=cv_data["email"],
        phone=cv_data.get("phone"),
        raw_text=cv_data["raw_text"],
        summary=cv_data.get("summary"),
        skills=cv_data.get("skills"),
        file_name=file.filename,
        file_type=cv_data["file_type"]
    )

    # Generate embedding
    try:
        embedding = embedding_service.generate(cv_data["raw_text"])
        cv.embedding = embedding
        cv.embedding_generated = True
        cv.embedding_generated_at = datetime.utcnow()
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        cv.embedding_generated = False

    db.add(cv)
    await db.commit()
    await db.refresh(cv)

    return cv


@router.get("/list", response_model=list[CVResponse], dependencies=[Depends(verify_secret_key)])
async def list_cvs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all CVs
    Requires: X-Secret-Key header
    """
    result = await db.execute(
        select(CV).offset(skip).limit(limit).order_by(CV.created_at.desc())
    )
    return result.scalars().all()

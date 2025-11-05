from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from app.db.session import get_db
from app.models.cv import CV
from app.schemas.cv import CVResponse
from app.services.cv_processor import CVProcessor
from app.services.embedding import embedding_service
from app.core.auth import verify_secret_key

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/upload",
    response_model=CVResponse,
    dependencies=[Depends(verify_secret_key)]
)
async def upload_cv(
    file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
    db: AsyncSession = Depends(get_db)
):
    """
    API 1: Upload CV and add to collection

    Upload a CV file (PDF or DOCX) using multipart/form-data.
    Automatically extracts: name, email, phone, skills, summary

    **Supported file types:**
    - PDF (.pdf)
    - DOCX (.docx, .doc)

    **Example using curl:**
    ```bash
    curl -X POST "http://localhost:8000/api/cv/upload" \\
      -H "X-Secret-Key: your-secret-key" \\
      -F "file=@/path/to/cv.pdf"
    ```

    **Example using Python requests:**
    ```python
    import requests
    with open('cv.pdf', 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/cv/upload',
            headers={'X-Secret-Key': 'your-secret-key'},
            files={'file': f}
        )
    ```
    """
    logger.info("=== CV Upload Request Started ===")
    logger.info(f"Filename: {file.filename}")
    logger.info(f"Content-Type: {file.content_type}")

    # Extract and parse CV
    logger.info("Starting CV extraction and parsing")
    try:
        cv_data = await CVProcessor.extract_and_parse(file)
        logger.info(f"CV extraction successful. Extracted data keys: {list(cv_data.keys())}")
    except Exception as e:
        logger.error(f"CV extraction failed: {str(e)}", exc_info=True)
        raise

    # Validate required fields
    logger.info("Validating required fields")
    if not cv_data.get("email"):
        preview = cv_data.get("raw_text", "")[:500] if cv_data.get("raw_text") else "No text extracted"
        logger.error(f"Email not found in CV. Text preview: {preview[:100]}...")
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract email from CV. Please ensure CV contains email address."
        )

    if not cv_data.get("candidate_name"):
        logger.error("Candidate name not found in CV")
        raise HTTPException(status_code=400, detail="Could not extract name from CV. Please ensure CV contains candidate name.")

    logger.info(f"Extracted candidate: {cv_data['candidate_name']}, email: {cv_data['email']}")

    # Check if email already exists
    logger.info(f"Checking if email already exists: {cv_data['email']}")
    result = await db.execute(select(CV).where(CV.email == cv_data["email"]))
    if result.scalar_one_or_none():
        logger.warning(f"CV with email {cv_data['email']} already exists")
        raise HTTPException(status_code=400, detail=f"CV with email {cv_data['email']} already exists")

    # Create CV
    logger.info("Creating CV record in database")
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
    logger.info("Generating embedding for CV text")
    try:
        text_length = len(cv_data["raw_text"])
        logger.info(f"Text length for embedding: {text_length} characters")
        embedding = embedding_service.generate(cv_data["raw_text"])
        cv.embedding = embedding
        cv.embedding_generated = True
        cv.embedding_generated_at = datetime.utcnow()
        logger.info(f"Embedding generated successfully. Dimension: {len(embedding)}")
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}", exc_info=True)
        cv.embedding_generated = False

    logger.info("Saving CV to database")
    db.add(cv)
    await db.commit()
    await db.refresh(cv)

    logger.info(f"=== CV Upload Successful === ID: {cv.id}, Name: {cv.candidate_name}, Email: {cv.email}")
    return cv


@router.get("/list", response_model=list[CVResponse], dependencies=[Depends(verify_secret_key)])
async def list_cvs(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all CVs with optional search
    Requires: X-Secret-Key header
    Query params:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    - search: Search by candidate name or email (optional)
    """
    logger.info(f"List CVs request - skip: {skip}, limit: {limit}, search: {search}")

    query = select(CV)

    # Add search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (CV.candidate_name.ilike(search_term)) |
            (CV.email.ilike(search_term))
        )
        logger.info(f"Applying search filter: {search_term}")

    query = query.offset(skip).limit(limit).order_by(CV.created_at.desc())
    result = await db.execute(query)
    cvs = result.scalars().all()

    logger.info(f"Returning {len(cvs)} CV records")
    return cvs

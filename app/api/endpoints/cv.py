from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Header
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


@router.post("/upload", response_model=CVResponse, dependencies=[Depends(verify_secret_key)])
async def upload_cv(
    request: Request,
    content_type: str = Header(..., alias="Content-Type"),
    content_disposition: str = Header(None, alias="Content-Disposition"),
    db: AsyncSession = Depends(get_db)
):
    """
    API 1: Upload CV and add to collection
    Accepts binary file content (PDF or DOCX)
    Automatically extracts: name, email, phone, skills, summary
    Requires: X-Secret-Key header, Content-Type header
    Content-Type should be: application/pdf or application/vnd.openxmlformats-officedocument.wordprocessingml.document
    """
    logger.info("=== CV Upload Request Started ===")
    logger.info(f"Content-Type: {content_type}")
    logger.info(f"Content-Disposition: {content_disposition}")

    # Read raw binary content
    file_content = await request.body()
    file_size = len(file_content)
    logger.info(f"File size: {file_size} bytes")

    if not file_content:
        logger.error("No file content provided")
        raise HTTPException(status_code=400, detail="No file content provided")

    # Normalize Content-Type (remove charset and other parameters)
    content_type_normalized = content_type.split(';')[0].strip().lower()
    logger.info(f"Normalized Content-Type: {content_type_normalized}")

    # Determine file type from Content-Type header
    if content_type_normalized == "application/pdf":
        file_type = "pdf"
        filename = "uploaded_cv.pdf"
        logger.info(f"Detected file type: PDF")
    elif content_type_normalized in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/docx"
    ]:
        file_type = "docx"
        filename = "uploaded_cv.docx"
        logger.info(f"Detected file type: DOCX")
    elif content_type_normalized in ["application/octet-stream", "binary/octet-stream"]:
        logger.info("Generic binary content-type, attempting file signature detection")
        # If generic binary type, try to detect from file signature
        file_signature = file_content[:4]
        logger.info(f"File signature (first 4 bytes): {file_signature}")

        if file_content[:4] == b'%PDF':
            file_type = "pdf"
            filename = "uploaded_cv.pdf"
            logger.info("File signature detected as PDF")
        elif file_content[:2] == b'PK':  # ZIP archive (DOCX is a ZIP file)
            file_type = "docx"
            filename = "uploaded_cv.docx"
            logger.info("File signature detected as DOCX (ZIP)")
        else:
            logger.error(f"Unknown file signature: {file_signature}")
            raise HTTPException(
                status_code=400,
                detail="Cannot determine file type. Please set Content-Type to 'application/pdf' or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
            )
    else:
        logger.error(f"Unsupported Content-Type: {content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported Content-Type: '{content_type}'. Use 'application/pdf' or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or 'application/octet-stream'"
        )

    # Extract filename from Content-Disposition if provided
    if content_disposition:
        import re
        filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
        if filename_match:
            filename = filename_match.group(1)
            logger.info(f"Extracted filename from Content-Disposition: {filename}")

    logger.info(f"Final filename: {filename}, file_type: {file_type}")

    # Create a file-like object for the processor
    from io import BytesIO
    file_obj = BytesIO(file_content)

    # Create a mock UploadFile object
    class MockUploadFile:
        def __init__(self, content, filename, content_type):
            self.file = BytesIO(content)
            self.filename = filename
            self.content_type = content_type

        async def read(self):
            return self.file.getvalue()

    mock_file = MockUploadFile(file_content, filename, content_type)

    # Extract and parse CV
    logger.info("Starting CV extraction and parsing")
    try:
        cv_data = await CVProcessor.extract_and_parse(mock_file)
        logger.info(f"CV extraction successful. Extracted data keys: {list(cv_data.keys())}")
    except Exception as e:
        logger.error(f"CV extraction failed: {str(e)}", exc_info=True)
        raise

    # Validate required fields
    logger.info("Validating required fields")
    if not cv_data.get("email"):
        # Show first 500 chars of text for debugging
        preview = cv_data.get("raw_text", "")[:500] if cv_data.get("raw_text") else "No text extracted"
        logger.error(f"Email not found in CV. Text preview: {preview[:100]}...")
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract email from CV. Please ensure CV contains email address. Text preview: {preview}..."
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
        file_name=filename,
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

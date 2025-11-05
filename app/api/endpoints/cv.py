from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Header
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
    # Read raw binary content
    file_content = await request.body()

    if not file_content:
        raise HTTPException(status_code=400, detail="No file content provided")

    # Normalize Content-Type (remove charset and other parameters)
    content_type_normalized = content_type.split(';')[0].strip().lower()

    # Determine file type from Content-Type header
    if content_type_normalized == "application/pdf":
        file_type = "pdf"
        filename = "uploaded_cv.pdf"
    elif content_type_normalized in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/docx"
    ]:
        file_type = "docx"
        filename = "uploaded_cv.docx"
    elif content_type_normalized in ["application/octet-stream", "binary/octet-stream"]:
        # If generic binary type, try to detect from file signature
        if file_content[:4] == b'%PDF':
            file_type = "pdf"
            filename = "uploaded_cv.pdf"
        elif file_content[:2] == b'PK':  # ZIP archive (DOCX is a ZIP file)
            file_type = "docx"
            filename = "uploaded_cv.docx"
        else:
            raise HTTPException(
                status_code=400,
                detail="Cannot determine file type. Please set Content-Type to 'application/pdf' or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
            )
    else:
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
    cv_data = await CVProcessor.extract_and_parse(mock_file)

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

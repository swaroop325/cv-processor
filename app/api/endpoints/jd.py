from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime

from app.db.session import get_db
from app.models.jd import JD
from app.models.cv import CV
from app.schemas.jd import JDCreate, JDResponse, FindBestCVsRequest, ContactCandidateRequest
from app.schemas.cv import CVMatch, CVResponse
from app.services.embedding import embedding_service
from app.services.email import EmailService
from app.core.auth import verify_secret_key

router = APIRouter()


@router.post("/create", response_model=JDResponse, dependencies=[Depends(verify_secret_key)])
async def create_jd(
    jd_data: JDCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    API 2: Create Job Description
    Accepts JSON with title and requirements
    Stores in database and generates embedding
    Requires: X-Secret-Key header
    """
    # Create JD text for embedding
    jd_text = f"{jd_data.title} {jd_data.requirements}"

    # Create JD
    jd = JD(
        title=jd_data.title,
        company=None,
        department=None,
        location=None,
        description=jd_data.requirements,
        requirements=jd_data.requirements,
        responsibilities=None,
        employment_type=None,
        experience_level=None
    )

    # Generate embedding
    try:
        embedding = embedding_service.generate(jd_text)
        jd.embedding = embedding
        jd.embedding_generated = True
        jd.embedding_generated_at = datetime.utcnow()
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        jd.embedding_generated = False

    db.add(jd)
    await db.commit()
    await db.refresh(jd)

    return jd


@router.get("/list", response_model=list[JDResponse], dependencies=[Depends(verify_secret_key)])
async def list_jds(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    search: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all job descriptions with optional search
    Requires: X-Secret-Key header
    Query params:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    - active_only: Only return active job descriptions (default: true)
    - search: Search by job title or requirements (optional)
    """
    query = select(JD)

    # Filter by active status
    if active_only:
        query = query.where(JD.is_active == True)

    # Add search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (JD.title.ilike(search_term)) |
            (JD.requirements.ilike(search_term))
        )

    query = query.offset(skip).limit(limit).order_by(JD.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/find-best-cvs", response_model=list[CVMatch], dependencies=[Depends(verify_secret_key)])
async def find_best_cvs(
    request: FindBestCVsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    API 3: Find best matching CVs for a JD
    Accepts JSON with jd_id and top_k
    Requires: X-Secret-Key header
    """
    # Get JD
    result = await db.execute(select(JD).where(JD.id == request.jd_id))
    jd = result.scalar_one_or_none()

    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    if not jd.embedding_generated or not jd.embedding:
        raise HTTPException(status_code=400, detail="JD embedding not available")

    # Find matching CVs using vector similarity
    embedding_str = f"[{','.join(map(str, jd.embedding))}]"

    query = text("""
        SELECT
            id, candidate_name, email, phone, raw_text, summary,
            skills, experience, education, file_name, file_type,
            embedding_generated, embedding_generated_at, created_at, updated_at,
            (1 - (embedding <=> CAST(:jd_embedding AS vector))) as similarity_score
        FROM cv
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:jd_embedding AS vector)
        LIMIT :limit
    """)

    result = await db.execute(query, {"jd_embedding": embedding_str, "limit": request.top_k})
    rows = result.fetchall()

    matches = []
    for row in rows:
        cv_data = {
            "id": row.id,
            "candidate_name": row.candidate_name,
            "email": row.email,
            "phone": row.phone,
            "raw_text": row.raw_text,
            "summary": row.summary,
            "skills": row.skills,
            "experience": row.experience,
            "education": row.education,
            "file_name": row.file_name,
            "file_type": row.file_type,
            "embedding_generated": row.embedding_generated,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        matches.append(CVMatch(cv=CVResponse(**cv_data), similarity_score=float(row.similarity_score)))

    return matches


@router.post("/contact-candidate", dependencies=[Depends(verify_secret_key)])
async def contact_candidate(
    request: ContactCandidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    API 4: Contact candidate via email
    Sends acceptance email with subject "Accepted"
    Accepts JSON with cv_id and jd_id
    Requires: X-Secret-Key header
    """
    # Get CV
    cv_result = await db.execute(select(CV).where(CV.id == request.cv_id))
    cv = cv_result.scalar_one_or_none()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Get JD
    jd_result = await db.execute(select(JD).where(JD.id == request.jd_id))
    jd = jd_result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="JD not found")

    # Create simple acceptance email
    subject = "Accepted"
    company = jd.company or "Our Company"
    body = f"""Dear {cv.candidate_name},

Congratulations! We are pleased to inform you that your application for the position of {jd.title} at {company} has been accepted.

We will contact you shortly with next steps.

Best regards,
{company} Recruitment Team"""

    email_sent = await EmailService.send_email(cv.email, subject, body)

    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {
        "message": "Acceptance email sent successfully",
        "candidate_email": cv.email,
        "candidate_name": cv.candidate_name,
        "job_title": jd.title
    }

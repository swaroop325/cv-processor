from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import cv, jd
from app.core.config import settings
from app.core.auth import verify_secret_key

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CV Processing Backend with vector similarity matching"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cv.router, prefix="/api/cv", tags=["CV"])
app.include_router(jd.router, prefix="/api/jd", tags=["JD"])


@app.get("/health", dependencies=[Depends(verify_secret_key)])
async def health():
    """
    Health check endpoint
    Requires: X-Secret-Key header
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

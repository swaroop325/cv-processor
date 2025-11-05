from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.api.endpoints import cv, jd
from app.core.config import settings
from app.core.auth import verify_secret_key

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CV Processing Backend with vector similarity matching"
)

# Include routers
app.include_router(cv.router, prefix="/api/cv", tags=["CV"])
app.include_router(jd.router, prefix="/api/jd", tags=["JD"])


# Custom OpenAPI schema to fix CV upload endpoint
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Override /api/cv/upload to show binary instead of multipart
    if "/api/cv/upload" in openapi_schema.get("paths", {}):
        openapi_schema["paths"]["/api/cv/upload"]["post"]["requestBody"] = {
            "required": True,
            "content": {
                "application/pdf": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                },
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                },
                "application/octet-stream": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

from fastapi import Header, HTTPException
from app.core.config import settings


async def verify_secret_key(x_secret_key: str = Header(..., alias="X-Secret-Key")):
    """
    Verify SECRET_KEY header for all API requests
    Header name: X-Secret-Key
    """
    if not settings.SECRET_KEY:
        raise HTTPException(status_code=500, detail="SECRET_KEY not configured on server")
    
    if x_secret_key != settings.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid SECRET_KEY")
    
    return True

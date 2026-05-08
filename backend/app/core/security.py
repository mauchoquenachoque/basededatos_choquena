from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.security import HTTPBearer
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    if not settings.API_KEY:
        return ""
    if api_key == settings.API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key.",
    )

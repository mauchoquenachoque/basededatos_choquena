from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_auth_service, get_current_active_user
from app.application.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.application.services.auth_service import AuthService
from app.domain.entities.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user.model_dump(exclude={"password_hash"}))


def _auth_response(payload: dict) -> AuthResponse:
    user = payload["user"]
    assert isinstance(user, User)
    return AuthResponse(
        access_token=str(payload["access_token"]),
        token_type=str(payload["token_type"]),
        user=_user_response(user),
    )


@router.post("/google", response_model=AuthResponse)
async def login_google(data: dict, auth_service: AuthService = Depends(get_auth_service)):
    """Expects JSON: { "id_token": "..." } (Google ID token from client)."""
    token = data.get("id_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing id_token")
    try:
        payload = await auth_service.authenticate_google(token)
        return _auth_response(payload)
    except ValueError as exc:
        if str(exc) == "INVALID_GOOGLE_TOKEN":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/me", response_model=UserResponse)
async def get_current_user(user: User = Depends(get_current_active_user)):
    return _user_response(user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(auth_service: AuthService = Depends(get_auth_service), current_user: User = Depends(get_current_active_user)):
    # Listing users remains protected by authentication; no admin roles.
    users = await auth_service._repository.get_all()
    return [_user_response(u) for u in users]

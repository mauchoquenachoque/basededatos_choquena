from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_auth_service, get_current_active_user, require_role
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


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        payload = await auth_service.register_local(data.email, data.password, data.name)
        return _auth_response(payload)
    except ValueError as exc:
        if str(exc) == "EMAIL_TAKEN":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cuenta con este correo.",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        payload = await auth_service.authenticate_local(data.email, data.password)
        return _auth_response(payload)
    except ValueError as exc:
        if str(exc) == "INVALID_CREDENTIALS":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos.",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/me", response_model=UserResponse)
async def get_current_user(user: User = Depends(get_current_active_user)):
    return _user_response(user)


@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_role("admin"))])
async def list_users(auth_service: AuthService = Depends(get_auth_service)):
    users = await auth_service._repository.get_all()
    return [_user_response(u) for u in users]

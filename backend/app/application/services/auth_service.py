import base64
import hashlib
import hmac
import json
import time
from typing import Dict, Optional

from app.core.config import settings
from app.core.passwords import hash_password, verify_password
from app.domain.entities.user import User
from app.domain.interfaces.repository import UserRepository
from app.infrastructure.repositories.user_repository import user_repository


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


class AuthService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        return await self._repository.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self._repository.get_by_email(email)

    async def register_local(self, email: str, password: str, name: str) -> Dict[str, object]:
        normalized = email.strip().lower()
        if await self.get_user_by_email(normalized):
            raise ValueError("EMAIL_TAKEN")

        display_name = name.strip() or normalized.split("@")[0]
        role = "admin" if normalized in {e.strip().lower() for e in settings.admin_emails_list()} else "user"

        user = User(
            email=normalized,
            name=display_name,
            role=role,
            picture=None,
            password_hash=hash_password(password),
        )
        user = await self._repository.create(user)
        return self._issue_auth_payload(user)

    async def authenticate_local(self, email: str, password: str) -> Dict[str, object]:
        normalized = email.strip().lower()
        user = await self.get_user_by_email(normalized)
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("INVALID_CREDENTIALS")
        return self._issue_auth_payload(user)

    def _issue_auth_payload(self, user: User) -> Dict[str, object]:
        access_token = self.create_access_token(
            subject=user.id or "",
            email=user.email,
            role=user.role,
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user,
        }

    def create_access_token(self, subject: str, email: str, role: str, expires_in: int = 3600) -> str:
        if not settings.SECRET_KEY:
            raise ValueError("SECRET_KEY is not configured.")

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": subject,
            "email": email,
            "role": role,
            "exp": int(time.time()) + expires_in,
        }
        header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        signature = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            f"{header_b64}.{payload_b64}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return f"{header_b64}.{payload_b64}.{_base64url_encode(signature)}"

    def verify_access_token(self, token: str) -> Dict[str, object]:
        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
        except ValueError:
            raise ValueError("Invalid token format.")

        expected_signature = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            f"{header_b64}.{payload_b64}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature = _base64url_decode(signature_b64)
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature.")

        payload = json.loads(_base64url_decode(payload_b64))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("Token has expired.")
        return payload

    async def get_current_user(self, token: str) -> User:
        payload = self.verify_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token subject is missing.")
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        return user


auth_service = AuthService(user_repository)

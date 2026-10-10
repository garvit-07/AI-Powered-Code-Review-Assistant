import asyncio
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


async def hash_password(password: str) -> str:
    """bcrypt is CPU-bound, so run it in a worker thread to keep the event loop free."""
    return await asyncio.to_thread(_hash, password)


async def verify_password(password: str, hashed: str) -> bool:
    return await asyncio.to_thread(_verify, password, hashed)


def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expires},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None

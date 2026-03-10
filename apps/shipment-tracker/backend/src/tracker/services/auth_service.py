"""Authentication and authorization service.

JWT-based auth with bcrypt password hashing and role-based access control.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
from loguru import logger

from tracker.config import get_settings

ROLES = {"admin", "trader", "operations", "viewer"}


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: str, email: str, role: str) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")


async def authenticate_user(conn, email: str, password: str) -> dict | None:
    """Authenticate a user by email and password. Returns user dict or None."""
    cursor = await conn.execute(
        "SELECT id, email, password_hash, full_name, role, is_active FROM users WHERE email = %s",
        [email],
    )
    user = await cursor.fetchone()
    if not user:
        return None

    if not user["is_active"]:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    # Update last_login
    await conn.execute(
        "UPDATE users SET last_login = NOW() WHERE id = %s",
        [str(user["id"])],
    )

    return user


async def register_user(
    conn,
    email: str,
    password: str,
    full_name: str,
    role: str = "viewer",
) -> dict:
    """Register a new user."""
    if role not in ROLES:
        raise ValueError(f"Invalid role: {role}. Must be one of {ROLES}")

    # Check if email already exists
    cursor = await conn.execute("SELECT id FROM users WHERE email = %s", [email])
    if await cursor.fetchone():
        raise ValueError("Email already registered")

    pw_hash = hash_password(password)

    cursor = await conn.execute(
        """
        INSERT INTO users (email, password_hash, full_name, role)
        VALUES (%s, %s, %s, %s)
        RETURNING id, email, full_name, role, is_active, created_at
        """,
        [email, pw_hash, full_name, role],
    )
    return await cursor.fetchone()


async def store_refresh_token(conn, user_id: str, token: str) -> None:
    """Store a refresh token in the database."""
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)

    await conn.execute(
        """
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
        VALUES (%s, %s, %s)
        """,
        [user_id, hash_password(token), expires_at],
    )


async def revoke_refresh_token(conn, token: str) -> bool:
    """Revoke a refresh token."""
    # Find and revoke the token
    cursor = await conn.execute(
        "SELECT id, token_hash FROM refresh_tokens WHERE revoked_at IS NULL AND expires_at > NOW()"
    )
    rows = await cursor.fetchall()
    for row in rows:
        if verify_password(token, row["token_hash"]):
            await conn.execute(
                "UPDATE refresh_tokens SET revoked_at = NOW() WHERE id = %s",
                [str(row["id"])],
            )
            return True
    return False


def check_permission(user_role: str, required_roles: set[str]) -> bool:
    """Check if a user role has the required permission."""
    # Admin has all permissions
    if user_role == "admin":
        return True
    return user_role in required_roles

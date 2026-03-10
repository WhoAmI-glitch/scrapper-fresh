"""Authentication API endpoints.

Login, register, token refresh, and user management.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, Field
from loguru import logger

from tracker.db import get_conn
from tracker.services.auth_service import (
    authenticate_user,
    register_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    store_refresh_token,
    revoke_refresh_token,
    check_permission,
)

router = APIRouter()


# ── Request/Response Models ───────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=200)
    role: str = "viewer"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Auth Dependency ───────────────────────────────────────────────────────────

async def get_current_user(authorization: str | None = Header(None)) -> dict:
    """Extract and validate the current user from the Authorization header."""
    if not authorization:
        raise HTTPException(401, "Authorization header required")

    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization format. Use 'Bearer <token>'")

    token = authorization[7:]
    try:
        payload = decode_token(token)
    except ValueError as e:
        raise HTTPException(401, str(e))

    if payload.get("type") != "access":
        raise HTTPException(401, "Invalid token type")

    return {
        "id": payload["sub"],
        "email": payload["email"],
        "role": payload["role"],
    }


def require_roles(*roles: str):
    """Dependency factory that checks user role."""
    async def checker(user: dict = Depends(get_current_user)):
        if not check_permission(user["role"], set(roles)):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return checker


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Authenticate and return access + refresh tokens."""
    async with get_conn() as conn:
        user = await authenticate_user(conn, body.email, body.password)
        if not user:
            raise HTTPException(401, "Invalid email or password")

        user_id = str(user["id"])
        access = create_access_token(user_id, user["email"], user["role"])
        refresh = create_refresh_token(user_id)

        await store_refresh_token(conn, user_id, refresh)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user={
            "id": user_id,
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    )


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest):
    """Register a new user and return tokens."""
    async with get_conn() as conn:
        try:
            user = await register_user(
                conn, body.email, body.password, body.full_name, body.role
            )
        except ValueError as e:
            raise HTTPException(400, str(e))

        user_id = str(user["id"])
        access = create_access_token(user_id, user["email"], user["role"])
        refresh = create_refresh_token(user_id)

        await store_refresh_token(conn, user_id, refresh)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user={
            "id": user_id,
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    )


@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    """Exchange a refresh token for a new access token."""
    try:
        payload = decode_token(body.refresh_token)
    except ValueError as e:
        raise HTTPException(401, str(e))

    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")

    user_id = payload["sub"]

    async with get_conn() as conn:
        # Get user info
        cursor = await conn.execute(
            "SELECT id, email, full_name, role, is_active FROM users WHERE id = %s",
            [user_id],
        )
        user = await cursor.fetchone()
        if not user or not user["is_active"]:
            raise HTTPException(401, "User not found or disabled")

        # Revoke old refresh token and issue new pair
        await revoke_refresh_token(conn, body.refresh_token)

        new_access = create_access_token(str(user["id"]), user["email"], user["role"])
        new_refresh = create_refresh_token(str(user["id"]))

        await store_refresh_token(conn, str(user["id"]), new_refresh)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(body: RefreshRequest):
    """Revoke a refresh token (logout)."""
    async with get_conn() as conn:
        await revoke_refresh_token(conn, body.refresh_token)
    return {"status": "logged out"}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get the current authenticated user."""
    async with get_conn() as conn:
        cursor = await conn.execute(
            "SELECT id, email, full_name, role, is_active, created_at, last_login FROM users WHERE id = %s",
            [user["id"]],
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, "User not found")

    return {
        "id": str(row["id"]),
        "email": row["email"],
        "full_name": row["full_name"],
        "role": row["role"],
        "is_active": row["is_active"],
        "created_at": str(row["created_at"]),
        "last_login": str(row["last_login"]) if row["last_login"] else None,
    }

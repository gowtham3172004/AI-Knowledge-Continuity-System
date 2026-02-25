"""
Supabase Client Module.

Provides a singleton Supabase client for database operations and
a FastAPI dependency for verifying Supabase JWT tokens.
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

from supabase import create_client, Client
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Auth scheme
security = HTTPBearer(auto_error=False)

# ---------- Supabase client singleton ----------

@lru_cache()
def get_supabase() -> Client:
    """Get the Supabase client (singleton)."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # service role for backend DB ops
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables"
        )
    return create_client(url, key)


def get_supabase_anon() -> Client:
    """Get a Supabase client using the anon key (for auth verification)."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables"
        )
    return create_client(url, key)


# ---------- FastAPI auth dependency ----------

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    FastAPI dependency: verify Supabase access token and return user info.

    The frontend sends the Supabase session access_token as a Bearer token.
    We verify it using Supabase's auth.get_user(token) which validates the JWT
    server-side against Supabase's auth service.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials
    try:
        sb = get_supabase()
        user_response = sb.auth.get_user(token)
        user = user_response.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {
            "id": user.id,  # Supabase UUID
            "email": user.email,
            "full_name": (user.user_metadata or {}).get("full_name", ""),
            "role": (user.user_metadata or {}).get("role", "developer"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Auth verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """Like get_current_user but returns None instead of raising."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

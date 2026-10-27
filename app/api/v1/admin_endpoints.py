import time
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.config import settings
from app.services import cache, upstream_client
from app.services.admin_auth import (
    create_admin_token,
    get_current_admin,
    verify_admin_credentials,
)
from app.services.upstream_client import AUTHORIZED_CHANNELS, AUTHORIZED_CATEGORIES

router = APIRouter(prefix="/admin", tags=["Admin Portal"])


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    token: str
    username: str
    expires_in_days: int = 7


class AdminChannelCreate(BaseModel):
    id: Optional[int] = None
    category_id: int
    name: str
    stream_url: str
    description: Optional[str] = "Live broadcast channel"
    logo: Optional[str] = None
    stream_format: str = "hls"


@router.post("/login", response_model=AdminLoginResponse, summary="Admin Login")
async def admin_login(payload: AdminLoginRequest, response: Response):
    if not verify_admin_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin username or password",
        )

    token = create_admin_token(payload.username)

    # Set httpOnly cookie for web dashboard browser session
    response.set_cookie(
        key="admin_token",
        value=token,
        max_age=86400 * 7,
        httponly=True,
        samesite="lax",
        secure=False,  # Set true if on production HTTPS
    )

    return AdminLoginResponse(
        success=True,
        token=token,
        username=payload.username,
        expires_in_days=7,
    )


@router.post("/logout", summary="Admin Logout")
async def admin_logout(response: Response):
    response.delete_cookie(key="admin_token")
    return {"success": True, "message": "Admin logged out successfully"}


@router.get("/stats", summary="Admin Server Statistics")
async def admin_stats(_admin: dict = Depends(get_current_admin)):
    categories = await upstream_client.get_categories()
    channels = await upstream_client.get_all_channels()
    health = await upstream_client.check_upstream_health_detailed()

    return {
        "success": True,
        "app_name": settings.app_name,
        "version": settings.version,
        "cache_entries": cache.size(),
        "total_categories": len(categories),
        "total_channels": len(channels),
        "active_mirror": health.get("active_mirror"),
        "upstream_available": health.get("upstream_available"),
        "tested_mirrors": health.get("tested_mirrors", []),
        "timestamp": time.time(),
    }


@router.post("/cache/flush", summary="Flush Server Cache")
async def flush_cache(_admin: dict = Depends(get_current_admin)):
    size_before = cache.size()
    cache.clear()
    return {
        "success": True,
        "message": f"Successfully flushed {size_before} cache entries",
        "cache_entries": 0,
    }


@router.post("/channels", summary="Add Custom Channel")
async def add_custom_channel(
    channel_data: AdminChannelCreate,
    _admin: dict = Depends(get_current_admin),
):
    channel_id = channel_data.id
    if not channel_id:
        existing_ids = list(AUTHORIZED_CHANNELS.keys())
        channel_id = max(existing_ids, default=100) + 1

    new_channel = {
        "id": channel_id,
        "category_id": channel_data.category_id,
        "name": channel_data.name,
        "logo": channel_data.logo
        or "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=150&q=80",
        "description": channel_data.description,
        "is_live": True,
        "stream_url": channel_data.stream_url,
        "stream_format": channel_data.stream_format,
        "headers": {"User-Agent": "LiveWaveTV-ExoPlayer/1.1"},
        "backup_streams": [],
    }

    AUTHORIZED_CHANNELS[channel_id] = new_channel
    cache.clear()  # Invalidate caches so app immediately sees new channel

    return {
        "success": True,
        "message": f"Channel '{channel_data.name}' added with ID {channel_id}",
        "channel": new_channel,
    }


@router.delete("/channels/{channel_id}", summary="Delete Channel")
async def delete_channel(
    channel_id: int,
    _admin: dict = Depends(get_current_admin),
):
    if channel_id in AUTHORIZED_CHANNELS:
        deleted = AUTHORIZED_CHANNELS.pop(channel_id)
        cache.clear()
        return {
            "success": True,
            "message": f"Channel '{deleted.get('name')}' (ID {channel_id}) removed",
        }
    raise HTTPException(
        status_code=404,
        detail=f"Channel {channel_id} not found in catalog",
    )


@router.get("/mirrors/test", summary="Test Upstream Mirrors Live")
async def test_upstream_mirrors(_admin: dict = Depends(get_current_admin)):
    detailed = await upstream_client.check_upstream_health_detailed()
    return detailed

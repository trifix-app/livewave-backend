import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Query

from app.models import (
    CategoryListResponse,
    CategoryDetailResponse,
    ChannelListResponse,
    ChannelDetailResponse,
    Category,
    ChannelSummary,
    ChannelDetail,
    SearchResponse,
    StreamStatusResponse,
    PingResponse,
    LiveMatch,
    MatchListResponse,
    ChannelEPGResponse,
    EPGListResponse,
)
import time


from app.services import cache, upstream_client
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/categories",
    response_model=CategoryListResponse,
    summary="Get all TV categories",
    description="Returns all available live TV categories with channel counts and preview artwork.",
)
async def get_categories():
    cache_key = "v1:categories"
    cached = cache.get(cache_key)
    if cached:
        return CategoryListResponse(
            success=True,
            total=len(cached),
            categories=[Category(**c) for c in cached],
        )

    categories_raw = await upstream_client.get_categories()
    cache.set(cache_key, categories_raw, ttl=settings.cache_ttl_seconds)

    return CategoryListResponse(
        success=True,
        total=len(categories_raw),
        categories=[Category(**c) for c in categories_raw],
    )


@router.get(
    "/categories/{category_id}",
    response_model=CategoryDetailResponse,
    summary="Get category details",
    description="Returns metadata for a specific TV category by its ID.",
)
async def get_category(
    category_id: int = Path(..., description="The ID of the category", ge=1)
):
    cache_key = f"v1:category:{category_id}"
    cached = cache.get(cache_key)
    if cached:
        return CategoryDetailResponse(
            success=True, category=Category(**cached)
        )

    cat = await upstream_client.get_category_by_id(category_id)
    if not cat:
        raise HTTPException(
            status_code=404,
            detail=f"Category with ID {category_id} not found",
        )

    cache.set(cache_key, cat, ttl=settings.cache_ttl_seconds)
    return CategoryDetailResponse(success=True, category=Category(**cat))


@router.get(
    "/categories/{category_id}/channels",
    response_model=ChannelListResponse,
    summary="Get channels in a category",
    description="Returns all live channels belonging to the specified category.",
)
async def get_category_channels(
    category_id: int = Path(..., description="The ID of the category", ge=1)
):
    cache_key = f"v1:category_channels:{category_id}"
    cached = cache.get(cache_key)
    if cached:
        cat_info = await upstream_client.get_category_by_id(category_id)
        cat_name = cat_info["name"] if cat_info else None
        return ChannelListResponse(
            success=True,
            category_id=category_id,
            category_name=cat_name,
            total=len(cached),
            channels=[ChannelSummary(**ch) for ch in cached],
        )

    channels_raw = await upstream_client.get_category_channels(category_id)
    cat_info = await upstream_client.get_category_by_id(category_id)
    cat_name = cat_info["name"] if cat_info else None

    cache.set(cache_key, channels_raw, ttl=settings.cache_ttl_seconds)

    return ChannelListResponse(
        success=True,
        category_id=category_id,
        category_name=cat_name,
        total=len(channels_raw),
        channels=[ChannelSummary(**ch) for ch in channels_raw],
    )


@router.get(
    "/channels/{channel_id}",
    response_model=ChannelDetailResponse,
    summary="Get channel details and stream URL",
    description="Retrieves channel metadata, live status, and playable stream URL.",
)
async def get_channel_detail(
    channel_id: int = Path(..., description="The ID of the channel", ge=1)
):
    cache_key = f"v1:channel:{channel_id}"
    cached = cache.get(cache_key)
    if cached:
        return ChannelDetailResponse(
            success=True, channel=ChannelDetail(**cached)
        )

    channel_raw = await upstream_client.get_channel_detail(channel_id)
    if not channel_raw:
        raise HTTPException(
            status_code=404,
            detail=f"Channel with ID {channel_id} not found or stream is currently unavailable",
        )

    # Cache channel metadata with shorter TTL for stream URL freshness
    cache.set(cache_key, channel_raw, ttl=min(settings.cache_ttl_seconds, 120))

    return ChannelDetailResponse(
        success=True, channel=ChannelDetail(**channel_raw)
    )


@router.get(
    "/ping",
    response_model=PingResponse,
    summary="Ping API endpoint",
    description="Returns connectivity status and server timestamp for latency testing.",
)
async def ping():
    return PingResponse(
        status="ok",
        timestamp=time.time(),
        message="pong",
        version=settings.version,
    )


@router.get(
    "/channels",
    response_model=ChannelListResponse,
    summary="Get all channels",
    description="Returns all live channels across all categories.",
)
async def get_all_channels():
    cache_key = "v1:all_channels"
    cached = cache.get(cache_key)
    if cached:
        return ChannelListResponse(
            success=True,
            category_id=0,
            category_name="All",
            total=len(cached),
            channels=[ChannelSummary(**ch) for ch in cached],
        )

    channels_raw = await upstream_client.get_all_channels()
    cache.set(cache_key, channels_raw, ttl=settings.cache_ttl_seconds)

    return ChannelListResponse(
        success=True,
        category_id=0,
        category_name="All",
        total=len(channels_raw),
        channels=[ChannelSummary(**ch) for ch in channels_raw],
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search channels",
    description="Fast keyword search across channel names and descriptions with optional category filter.",
)
async def search_channels(
    q: str = Query(..., min_length=1, description="Search keyword"),
    category_id: Optional[int] = Query(None, description="Optional category ID to filter by"),
):
    results = await upstream_client.search_channels(q, category_id=category_id)
    return SearchResponse(
        success=True,
        query=q,
        total=len(results),
        channels=[ChannelSummary(**ch) for ch in results],
    )


@router.get(
    "/channels/{channel_id}/status",
    response_model=StreamStatusResponse,
    summary="Probe channel live stream status",
    description="Actively checks if a channel's stream endpoint responds with valid HLS stream headers and measures latency.",
)
async def probe_channel_stream_status(
    channel_id: int = Path(..., description="The ID of the channel", ge=1)
):
    probe_result = await upstream_client.probe_stream(channel_id)
    if not probe_result:
        raise HTTPException(
            status_code=404,
            detail=f"Channel {channel_id} has no stream configured or does not exist",
        )

    return StreamStatusResponse(**probe_result)


@router.get(
    "/matches",
    response_model=MatchListResponse,
    summary="Get today's live sports matches",
    description="Returns list of today's live and upcoming football games with teams, tournaments, live scores, and linked streaming channel IDs.",
)
async def get_matches():
    cache_key = "v1:matches"
    cached = cache.get(cache_key)
    if cached:
        return MatchListResponse(
            success=True,
            total=len(cached),
            matches=[LiveMatch(**m) for m in cached],
        )

    matches_raw = await upstream_client.get_live_matches()
    cache.set(cache_key, matches_raw, ttl=60)  # Shorter 60s cache for live scores

    return MatchListResponse(
        success=True,
        total=len(matches_raw),
        matches=[LiveMatch(**m) for m in matches_raw],
    )


@router.get(
    "/channels/{channel_id}/epg",
    response_model=ChannelEPGResponse,
    summary="Get channel Electronic Program Guide (EPG)",
    description="Returns real-time program information, current on-air show with progress %, and full 24h schedule.",
)
async def get_channel_epg(
    channel_id: int = Path(..., description="The ID of the channel", ge=1)
):
    epg = await upstream_client.get_channel_epg(channel_id)
    if not epg:
        raise HTTPException(
            status_code=404,
            detail=f"Channel {channel_id} not found or has no program schedule",
        )
    return ChannelEPGResponse(**epg)


@router.get(
    "/epg",
    response_model=EPGListResponse,
    summary="Get real-time TV guide across all channels",
    description="Returns current live programs and upcoming schedules for all available channels.",
)
async def get_all_epg():
    epg_list = await upstream_client.get_all_epg()
    return EPGListResponse(
        success=True,
        total=len(epg_list),
        epg=[ChannelEPGResponse(**e) for e in epg_list],
    )




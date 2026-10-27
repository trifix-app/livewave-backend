from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Category(BaseModel):
    id: int
    name: str
    image: Optional[str] = None
    channel_count: Optional[int] = 0


class CategoryListResponse(BaseModel):
    success: bool = True
    total: int
    categories: List[Category]


class CategoryDetailResponse(BaseModel):
    success: bool = True
    category: Category


class ChannelSummary(BaseModel):
    id: int
    category_id: int
    name: str
    logo: Optional[str] = None
    description: Optional[str] = None
    is_live: bool = True
    stream_format: str = "hls"
    current_program: Optional[str] = None
    current_program_time: Optional[str] = None
    current_program_progress: Optional[int] = None


class ChannelListResponse(BaseModel):
    success: bool = True
    category_id: int
    category_name: Optional[str] = None
    total: int
    channels: List[ChannelSummary]


class StreamSource(BaseModel):
    url: str
    format: str = "hls"  # hls, mp4, etc.
    quality: Optional[str] = "auto"
    headers: Optional[Dict[str, str]] = None


class ChannelDetail(BaseModel):
    id: int
    category_id: int
    name: str
    logo: Optional[str] = None
    description: Optional[str] = None
    is_live: bool = True
    stream_url: Optional[str] = None
    stream_format: str = "hls"
    headers: Optional[Dict[str, str]] = None
    backup_streams: List[StreamSource] = Field(default_factory=list)
    current_program: Optional[str] = None
    current_program_time: Optional[str] = None
    current_program_progress: Optional[int] = None


class ChannelDetailResponse(BaseModel):
    success: bool = True
    channel: ChannelDetail


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    upstream_url: str
    upstream_available: bool
    fallback_active: bool
    cache_entries: int
    active_mirror: Optional[str] = None
    tested_mirrors: List[Dict[str, Any]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None


class PingResponse(BaseModel):
    status: str = "ok"
    timestamp: float
    message: str = "pong"
    version: str = "1.0.0"


class StreamStatusResponse(BaseModel):
    channel_id: int
    channel_name: str
    stream_url: str
    is_reachable: bool
    http_status: Optional[int] = None
    latency_ms: Optional[float] = None
    content_type: Optional[str] = None
    is_hls: bool = False
    checked_at: float


class SearchResponse(BaseModel):
    success: bool = True
    query: str
    total: int
    channels: List[ChannelSummary]


class LiveMatch(BaseModel):
    id: int
    home_team: str
    away_team: str
    home_logo: Optional[str] = None
    away_logo: Optional[str] = None
    tournament: str
    match_time: str
    status: str = "live"  # 'live', 'upcoming', 'finished'
    score: Optional[str] = None
    minute: Optional[str] = None
    channel_id: int
    channel_name: str


class MatchListResponse(BaseModel):
    success: bool = True
    total: int
    matches: List[LiveMatch]


class ProgramItem(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    start_time: str
    end_time: str
    progress_percent: int = 0
    is_live: bool = False
    category: Optional[str] = None
    time_remaining: Optional[str] = None


class ChannelEPGResponse(BaseModel):
    success: bool = True
    channel_id: int
    channel_name: str
    current_program: Optional[ProgramItem] = None
    next_program: Optional[ProgramItem] = None
    schedule: List[ProgramItem] = Field(default_factory=list)


class EPGListResponse(BaseModel):
    success: bool = True
    total: int
    epg: List[ChannelEPGResponse]



import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api import v1_router
from app.admin_web import admin_web_router
from app.models import HealthResponse, ErrorResponse
from app.services import cache, upstream_client


# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("livewave_backend")

app = FastAPI(
    title=settings.app_name,
    description="Production-grade Live TV API wrapper for LiveWave TV Flutter Android application.",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for cross-origin testing and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


@app.get("/", summary="Root index")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "healthy",
        "docs": "/docs",
        "api_v1": "/api/v1",
    }


@app.get("/ping", summary="Quick server ping")
async def ping():
    return {"status": "ok", "timestamp": time.time(), "message": "pong", "version": settings.version}


@app.get("/health", response_model=HealthResponse, summary="Service health check")
@app.get("/api/v1/health", response_model=HealthResponse, summary="API v1 health check")
async def health_check():
    detailed = await upstream_client.check_upstream_health_detailed()
    upstream_ok = detailed["upstream_available"]
    return HealthResponse(
        status="ok",
        version=settings.version,
        upstream_url=settings.upstream_base_url,
        upstream_available=upstream_ok,
        fallback_active=not upstream_ok and settings.enable_authorized_fallback,
        cache_entries=cache.size(),
        active_mirror=detailed.get("active_mirror"),
        tested_mirrors=detailed.get("tested_mirrors", []),
    )



# Include API v1 router
app.include_router(v1_router)

# Include Admin Web UI
app.include_router(admin_web_router)



@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="Internal Server Error",
            detail="An unexpected error occurred while processing your request.",
        ).model_dump(),
    )


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)


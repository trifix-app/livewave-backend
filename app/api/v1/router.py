from fastapi import APIRouter
from .endpoints import router as endpoints_router
from .admin_endpoints import router as admin_router

router = APIRouter(prefix="/api/v1")
router.include_router(endpoints_router, tags=["LiveWave TV"])
router.include_router(admin_router)


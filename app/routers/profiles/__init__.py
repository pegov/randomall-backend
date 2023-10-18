from fastapi import APIRouter

from app.routers.profiles import admin, gens, info, lists, notifications

router = APIRouter()

router.include_router(admin.router, prefix="/api/users")
router.include_router(info.router, prefix="/api/users")
router.include_router(gens.router, prefix="/api/users")
router.include_router(lists.router, prefix="/api/users")
router.include_router(notifications.router, prefix="/api/users/me")

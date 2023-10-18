from fastapi import APIRouter

from app.routers.general import gens, usergen, wp

API_GENERAL_PREFIX = "/api/general"

router = APIRouter()

router.include_router(usergen.router, prefix=API_GENERAL_PREFIX)
router.include_router(wp.router, prefix=API_GENERAL_PREFIX)
router.include_router(gens.router, prefix=API_GENERAL_PREFIX)

"""
GET  ""

GET  /usergen
POST /usergen


GET  /usergen/stats
GET  /usergen/status
GET  /usergen/last
POST /usergen/toggle
GET  /usergen/wp
POST /usergen/wp
POST /usergen/suggest


GET  /{title}
POST /{title}
"""

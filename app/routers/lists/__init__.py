from fastapi import APIRouter

from app.config import API_LISTS_PREFIX
from app.routers.lists import admin, editor, search, view

router = APIRouter()

router.include_router(search.router, prefix=API_LISTS_PREFIX)
router.include_router(editor.router, prefix=API_LISTS_PREFIX)
router.include_router(admin.router, prefix=API_LISTS_PREFIX)
router.include_router(view.router, prefix=API_LISTS_PREFIX)

"""

GET    /lists - search
POST   /lists - editor


GET    /lists/status - editor

GET    /lists/profile - search

GET    /lists/stats - admin
GET    /lists/settings - admin
PUT    /lists/settings - admin


GET    /lists/{id} - view
PUT    /lists/{id} - editor
DELETE /lists/{id} - editor

GET    /lists/{id}/edit - editor
"""

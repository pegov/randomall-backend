from fastapi import APIRouter

from app.config import API_GENS_PREFIX
from app.routers.gens import admin, editor, search, view

router = APIRouter()

router.include_router(search.router, prefix=API_GENS_PREFIX)
router.include_router(editor.router, prefix=API_GENS_PREFIX)
router.include_router(admin.router, prefix=API_GENS_PREFIX)
router.include_router(view.router, prefix=API_GENS_PREFIX)

"""
GET    / - search
POST   / - editor

GET    /categories - search
GET    /subcategories - search
GET    /titles - search
GET    /tags - search

GET    /ping - admin
POST   /ping - editor
GET    /status - editor

GET    /suggestions - search
GET    /preview - search

GET    /profile - search
GET    /profile/favs - search

GET    /stats - admin
GET    /settings - admin
PUT    /settings - admin


GET    /{id} - view
POST   /{id} - view
PUT    /{id} - editor
DELETE /{id} - editor

GET    /{id}/edit - editor
POST   /{id}/key - editor

GET    /{id}/social - view
POST   /{id}/like - view
POST   /{id}/fav - view


GET    /{id}/{secret} - view
POST   /{id}/{secret} - view

"""

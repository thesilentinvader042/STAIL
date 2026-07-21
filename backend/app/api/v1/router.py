"""
app/api/v1/router.py
Central router — mounts all domain routers under /api/v1/.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import agents, auth, developers, leads, properties, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(properties.router)
api_router.include_router(leads.router)
api_router.include_router(agents.router)
api_router.include_router(developers.router, prefix="/developers", tags=["Developers"])
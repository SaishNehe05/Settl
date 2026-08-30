from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.cases import router as cases_router
from app.api.v1.policies import router as policies_router
from app.api.v1.events import router as events_router
from app.api.v1.webhooks import router as webhooks_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(cases_router)
api_v1_router.include_router(policies_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(webhooks_router)

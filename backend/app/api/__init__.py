from fastapi import APIRouter

from app.api.audit import router as audit_router
from app.api.baselines import router as baselines_router
from app.api.evaluation import router as evaluation_router
from app.api.events import router as events_router
from app.api.features import router as features_router
from app.api.health import router as health_router
from app.api.interventions import router as interventions_router
from app.api.risk import router as risk_router
from app.api.scenarios import router as scenarios_router
from app.api.sessions import router as sessions_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(scenarios_router)
api_router.include_router(sessions_router)
api_router.include_router(events_router)
api_router.include_router(features_router)
api_router.include_router(risk_router)
api_router.include_router(interventions_router)
api_router.include_router(baselines_router)
api_router.include_router(audit_router)
api_router.include_router(evaluation_router)

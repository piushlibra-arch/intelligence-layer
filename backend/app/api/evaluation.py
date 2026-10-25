from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.security import require_api_key
from app.schemas.evaluation import EvaluationSummaryResponse
from app.engine.evaluation_engine import EvaluationEngine

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.get("/summary", response_model=EvaluationSummaryResponse)
async def get_evaluation_summary(db: AsyncSession = Depends(get_db)):
    return await EvaluationEngine.run_evaluation(db)

@router.post("/runs", response_model=EvaluationSummaryResponse)
async def start_evaluation_run(
    db: AsyncSession = Depends(get_db),
    _api_key: str = Depends(require_api_key)
):
    return await EvaluationEngine.run_evaluation(db)

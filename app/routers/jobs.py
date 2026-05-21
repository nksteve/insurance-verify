from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.verification_service import run_daily_verification

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/run-verification", summary="Manually trigger the daily verification run")
async def trigger_verification(db: AsyncSession = Depends(get_db)):
    return await run_daily_verification(db)

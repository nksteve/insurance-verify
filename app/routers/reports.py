from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import ActionQueueItem
from app.services.report_generator import get_action_queue, get_weekly_roi

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/action-queue", summary="Prioritized action queue for billing coordinator")
async def action_queue(include_resolved: bool = False, db: AsyncSession = Depends(get_db)):
    return await get_action_queue(db, include_resolved)


@router.patch("/action-queue/{item_id}/resolve", summary="Mark an action item resolved")
async def resolve_item(item_id: int, resolved_by: str = "staff", db: AsyncSession = Depends(get_db)):
    item = await db.get(ActionQueueItem, item_id)
    if not item:
        raise HTTPException(404, "Action item not found")
    item.resolved = True
    item.resolved_at = datetime.utcnow()
    item.resolved_by = resolved_by
    await db.commit()
    return {"id": item_id, "resolved": True, "resolved_by": resolved_by}


@router.get("/weekly-roi", summary="Weekly ROI report — generated every Friday")
async def weekly_roi(db: AsyncSession = Depends(get_db)):
    return await get_weekly_roi(db)

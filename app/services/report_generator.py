from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActionQueueItem, Appointment, Patient, Priority

_PRIORITY_ORDER = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
    Priority.INFO: 4,
}

# MGMA 2023: average cost to rework a denied claim
_DENIED_CLAIM_COST = 127.0


async def get_action_queue(db: AsyncSession, include_resolved: bool = False) -> list:
    stmt = (
        select(ActionQueueItem, Appointment, Patient)
        .join(Appointment, ActionQueueItem.appointment_id == Appointment.id)
        .join(Patient, Appointment.patient_id == Patient.id)
        .order_by(ActionQueueItem.priority, Appointment.appointment_date)
    )
    if not include_resolved:
        stmt = stmt.where(ActionQueueItem.resolved == False)  # noqa: E712

    rows = (await db.execute(stmt)).all()

    items = [
        {
            "id": action.id,
            "priority": action.priority.value,
            "flag_type": action.flag_type,
            "description": action.description,
            "recommended_action": action.recommended_action,
            "appointment_date": appt.appointment_date.isoformat(),
            "service_type": appt.service_type,
            "patient_ref": f"PT-{patient.internal_id}",  # internal ID only — no name/DOB in API response
            "payer": patient.payer_name,
            "resolved": action.resolved,
            "created_at": action.created_at.isoformat(),
        }
        for action, appt, patient in rows
    ]

    return sorted(items, key=lambda x: _PRIORITY_ORDER.get(Priority(x["priority"]), 99))


async def get_weekly_roi(db: AsyncSession) -> dict:
    week_ago = datetime.utcnow() - timedelta(days=7)

    total = (await db.execute(
        select(func.count()).select_from(ActionQueueItem)
        .where(ActionQueueItem.created_at >= week_ago)
    )).scalar_one()

    resolved = (await db.execute(
        select(func.count()).select_from(ActionQueueItem)
        .where(ActionQueueItem.created_at >= week_ago, ActionQueueItem.resolved == True)  # noqa: E712
    )).scalar_one()

    critical = (await db.execute(
        select(func.count()).select_from(ActionQueueItem)
        .where(ActionQueueItem.created_at >= week_ago, ActionQueueItem.priority == Priority.CRITICAL)
    )).scalar_one()

    return {
        "period_start": week_ago.date().isoformat(),
        "period_end": datetime.utcnow().date().isoformat(),
        "total_flags_raised": total,
        "flags_resolved": resolved,
        "critical_flags": critical,
        "resolution_rate": f"{resolved / total * 100:.1f}%" if total else "0%",
        "estimated_value_protected": f"${resolved * _DENIED_CLAIM_COST:,.2f}",
        "note": "Estimated value based on $127 avg cost to rework a denied claim (MGMA 2023)",
    }

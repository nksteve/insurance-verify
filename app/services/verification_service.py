import csv
import io
import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ActionQueueItem, Appointment, AuditLog, EligibilityStatus, Patient, VerificationResult,
)
from app.services import pverify_client, rules_engine

logger = logging.getLogger(__name__)


async def ingest_csv(content: bytes, db: AsyncSession, performed_by: str = "system") -> dict:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    created = 0

    for row in reader:
        result = await db.execute(select(Patient).where(Patient.internal_id == row["patient_id"]))
        patient = result.scalar_one_or_none()

        if not patient:
            patient = Patient(
                internal_id=row["patient_id"],
                payer_id=row["payer_id"],
                payer_name=row["payer_name"],
                insurance_member_id=row["member_id"],
            )
            db.add(patient)
            await db.flush()

        appt = Appointment(
            patient_id=patient.id,
            appointment_date=datetime.fromisoformat(row["appointment_date"]),
            provider_npi=row["provider_npi"],
            service_type=row["service_type"],
        )
        db.add(appt)
        created += 1

    db.add(AuditLog(
        event_type="CSV_INGESTED",
        resource_type="appointments",
        performed_by=performed_by,
        details=json.dumps({"appointments_created": created}),
    ))
    await db.commit()

    logger.info("CSV ingestion complete appointments_created=%d performed_by=%s", created, performed_by)
    return {"appointments_created": created}


async def run_daily_verification(db: AsyncSession) -> dict:
    logger.info("Daily verification job started")

    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.patient))
        .outerjoin(VerificationResult, Appointment.id == VerificationResult.appointment_id)
        .where(VerificationResult.id == None)  # noqa: E711
        .order_by(Appointment.appointment_date)
    )
    appointments = result.scalars().all()

    processed = 0
    flags_created = 0

    for appt in appointments:
        patient = appt.patient
        try:
            response = await pverify_client.check_eligibility(
                member_id=patient.insurance_member_id,
                payer_id=patient.payer_id,
                service_type=appt.service_type,
                provider_npi=appt.provider_npi,
            )

            if response.not_found:
                status = EligibilityStatus.NOT_FOUND
            elif response.is_active:
                status = EligibilityStatus.ACTIVE
            else:
                status = EligibilityStatus.INACTIVE

            db.add(VerificationResult(
                appointment_id=appt.id,
                eligibility_status=status,
                deductible_individual=response.deductible_individual,
                deductible_met=response.deductible_met,
                copay=response.copay,
                coinsurance=response.coinsurance,
                out_of_pocket_max=response.out_of_pocket_max,
                out_of_pocket_met=response.out_of_pocket_met,
                prior_auth_required=response.prior_auth_required,
                in_network=response.in_network,
                payer_response_id=response.response_id,
            ))

            flags = rules_engine.evaluate(response, appt.service_type)
            for flag in flags:
                db.add(ActionQueueItem(
                    appointment_id=appt.id,
                    priority=flag.priority,
                    flag_type=flag.flag_type,
                    description=flag.description,
                    recommended_action=flag.recommended_action,
                ))
                flags_created += 1

            processed += 1

        except Exception as exc:
            logger.error(
                "Verification failed appointment_id=%d error_type=%s",
                appt.id, type(exc).__name__,
            )

    db.add(AuditLog(
        event_type="DAILY_VERIFICATION_COMPLETE",
        resource_type="appointments",
        details=json.dumps({"processed": processed, "flags_created": flags_created}),
    ))
    await db.commit()

    logger.info("Daily verification complete processed=%d flags=%d", processed, flags_created)
    return {"appointments_processed": processed, "flags_created": flags_created}

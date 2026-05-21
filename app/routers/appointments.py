from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.verification_service import ingest_csv

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/upload", summary="Upload appointment CSV for the day")
async def upload_appointments(
    file: UploadFile = File(..., description="CSV with columns: patient_id, payer_id, payer_name, member_id, appointment_date, provider_npi, service_type"),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "File must be a CSV")
    content = await file.read()
    return await ingest_csv(content, db)

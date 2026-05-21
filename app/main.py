import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from app.core.logging_config import setup_logging
from app.database import AsyncSessionLocal, init_db
from app.routers import appointments, jobs, reports
from app.services.verification_service import run_daily_verification

setup_logging()
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _scheduled_verification():
    logger.info("Scheduler: starting daily verification run")
    async with AsyncSessionLocal() as db:
        await run_daily_verification(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # 6am — run eligibility checks so action queue is ready well before 5pm delivery
    scheduler.add_job(_scheduled_verification, CronTrigger(hour=6, minute=0), id="daily_6am")
    # 7am — morning re-check alert for any overnight changes
    scheduler.add_job(_scheduled_verification, CronTrigger(hour=7, minute=0), id="recheck_7am")
    scheduler.start()
    logger.info("Insurance verification service started scheduler=active")
    yield
    scheduler.shutdown()
    logger.info("Insurance verification service stopped")


app = FastAPI(
    title="Insurance Eligibility Verification API",
    description=(
        "Pre-visit insurance verification for independent specialty practices. "
        "Ingests daily appointment schedules, runs pVerify eligibility checks, "
        "applies a rules engine to flag coverage problems, and delivers a prioritized "
        "action queue to the billing coordinator by 5pm — 48-72 hours before each visit."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(appointments.router)
app.include_router(jobs.router)
app.include_router(reports.router)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy"}

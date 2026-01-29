from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

logger = logging.getLogger(__name__)

from app.settings import settings
from app.db import init_db, async_session_maker
from app.auth.routes import router as auth_router
from app.api.routes import router as api_router
from app.realtime.routes import router as ws_router
from app.services.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Initialize database
    await init_db()

    # Seed data
    async with async_session_maker() as db:
        await seed_database(db)

    scheduler = None
    if settings.reminder_enabled:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        from app.services.notifications import check_due_date_reminders

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            check_due_date_reminders,
            CronTrigger(hour="11,16", timezone="Europe/Berlin"),
            id="due_date_reminders",
        )
        scheduler.start()
        logger.info("Due date reminder scheduler started (11:00 and 16:00 CET)")

    yield

    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Looma - Shared Todo App",
    description="Real-time shared todo app for two users",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = [origin.strip() for origin in settings.cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router, prefix="/api")
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

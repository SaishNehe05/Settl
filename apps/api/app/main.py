from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_v1_router
from app.database import engine, Base, SessionLocal
import app.models  # Ensure all models are registered

# Ensure tables exist (Alembic manages migrations)
if settings.sqlalchemy_database_url.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)

import asyncio
from contextlib import asynccontextmanager
from app.services.abandonment_worker import abandonment_worker_loop
from app.services.overdue_worker import detect_overdue_invoices
from app.services.promise_worker import promise_lifecycle_worker
from app.services.webhook_worker import webhook_retry_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB (in production, use Alembic)
    engine = SessionLocal().get_bind()
    Base.metadata.create_all(bind=engine)
    
    # Start background workers
    abandonment_task = asyncio.create_task(abandonment_worker_loop())
    overdue_task = asyncio.create_task(detect_overdue_invoices())
    promise_task = asyncio.create_task(promise_lifecycle_worker())
    webhook_task = asyncio.create_task(webhook_retry_worker())
    yield
    # Shutdown background workers
    abandonment_task.cancel()
    overdue_task.cancel()
    promise_task.cancel()
    webhook_task.cancel()
    try:
        await abandonment_task
        await overdue_task
        await promise_task
        await webhook_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous AI Revenue Recovery Agent API — Track 03 Razorpay Buildathon",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "Settl API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Mount API routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

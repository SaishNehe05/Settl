from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_v1_router
from app.database import engine, Base
import app.models  # Ensure all models are registered

# Ensure tables exist (Alembic manages migrations)
if settings.sqlalchemy_database_url.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous AI Revenue Recovery Agent API — Track 03 Razorpay Buildathon",
    docs_url="/docs",
    redoc_url="/redoc",
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

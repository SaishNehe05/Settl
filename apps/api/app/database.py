from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

connect_args = {}
db_url = settings.sqlalchemy_database_url

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Disable psycopg3 prepared statements for Supabase Transaction Pooler (PgBouncer)
    connect_args = {"prepare_threshold": None}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides an isolated transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

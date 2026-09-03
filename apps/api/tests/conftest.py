import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.scripts.seed_db import seed

# Import all models to ensure they are registered with Base.metadata
from app.models.merchant import Merchant
from app.models.policy import Policy
from app.models.customer import Customer
from app.models.order import Order
from app.models.payment import Payment
from app.models.revenue_event import RevenueEvent
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.audit_log import AuditLog
from app.models.webhook_event import WebhookEvent
from app.models.notification import Notification
from app.models.model_prediction import ModelPrediction
from app.models.promise import Promise

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    settings.RAZORPAY_KEY_ID = "rzp_test_placeholder"
    settings.RAZORPAY_KEY_SECRET = "placeholder_webhook_secret"
    settings.RAZORPAY_WEBHOOK_SECRET = "placeholder_webhook_secret"
    Base.metadata.create_all(bind=engine)
    
    # Patch database module so background tasks use the test DB
    import app.database as app_db
    app_db.engine = engine
    app_db.SessionLocal = TestingSessionLocal
    
    # Patch session in seed and run
    import app.scripts.seed_db as seed_module
    seed_module.engine = engine
    seed_module.SessionLocal = TestingSessionLocal
    seed()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

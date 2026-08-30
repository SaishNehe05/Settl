from datetime import datetime, timezone
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer
from app.models.order import Order
from app.models.recovery_case import RecoveryCase
from app.models.base import generate_uuid
from app.schemas.event import EventCreate
from app.services.recovery_service import create_case_for_event, execute_case_pipeline


def ingest_revenue_event(
    db: Session,
    data: EventCreate,
    merchant_id: str,
    auto_pipeline: bool = True
) -> Tuple[RevenueEvent, RecoveryCase]:
    """
    Ingests and normalizes an incoming revenue loss event with idempotency protection.
    Provisions or matches Customer and Order, creates RevenueEvent, and triggers the recovery pipeline.
    """
    # 1. Idempotency check: if event_id already exists for merchant, return existing
    if data.event_id:
        existing_event = (
            db.query(RevenueEvent)
            .filter(RevenueEvent.id == data.event_id, RevenueEvent.merchant_id == merchant_id)
            .first()
        )
        if existing_event:
            existing_case = (
                db.query(RecoveryCase)
                .filter(RecoveryCase.revenue_event_id == existing_event.id)
                .first()
            )
            return existing_event, existing_case

    # 2. Resolve or provision Customer
    customer = None
    if data.customer_id:
        customer = (
            db.query(Customer)
            .filter(Customer.id == data.customer_id, Customer.merchant_id == merchant_id)
            .first()
        )

    if not customer and data.customer_email:
        customer = (
            db.query(Customer)
            .filter(Customer.email == data.customer_email, Customer.merchant_id == merchant_id)
            .first()
        )

    if not customer:
        customer = Customer(
            id=generate_uuid("CUS"),
            merchant_id=merchant_id,
            name=data.customer_name or "Anonymous Customer",
            email=data.customer_email or f"customer_{generate_uuid()}@example.com",
            phone=data.customer_phone or "+919876543210",
            success_rate=0.85,
            customer_value="MEDIUM",
            opted_out=False,
        )
        db.add(customer)
        db.flush()

    # 3. Resolve or provision Order
    order = None
    if data.order_id:
        order = (
            db.query(Order)
            .filter(Order.id == data.order_id, Order.merchant_id == merchant_id)
            .first()
        )

    if not order:
        order = Order(
            id=data.order_id or generate_uuid("ORD"),
            merchant_id=merchant_id,
            customer_id=customer.id,
            amount_paise=data.amount_paise,
            currency=data.currency or "INR",
            status="PAYMENT_FAILED" if data.event_type == "PAYMENT_FAILED" else "ABANDONED",
        )
        db.add(order)
        db.flush()

    # 4. Create RevenueEvent
    event_id = data.event_id or generate_uuid("EVT")
    revenue_event = RevenueEvent(
        id=event_id,
        merchant_id=merchant_id,
        customer_id=customer.id,
        order_id=order.id,
        event_type=data.event_type,
        amount_paise=data.amount_paise,
        failure_reason=data.failure_reason,
        source=data.source or "synthetic",
        occurred_at=data.occurred_at or datetime.now(timezone.utc),
        raw_payload=data.raw_payload or {"source": data.source},
    )
    db.add(revenue_event)
    db.flush()

    # 5. Initialize RecoveryCase
    case = create_case_for_event(db, revenue_event)

    # 6. Execute deterministic analysis & policy evaluation pipeline
    if auto_pipeline:
        case = execute_case_pipeline(db, case.id)

    db.commit()
    db.refresh(revenue_event)
    db.refresh(case)
    return revenue_event, case

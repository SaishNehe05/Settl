from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ReceivableEventCreate(BaseModel):
    event_id: str = Field(..., description="Unique event ID from merchant billing/ERP system")
    merchant_id: Optional[str] = Field(None, description="Settl Merchant ID (must match auth credentials)")
    invoice_id: str = Field(..., description="Merchant invoice identifier (e.g. INV-2026-001)")
    customer_id: Optional[str] = Field(None, description="Merchant customer identifier")
    customer_name: Optional[str] = Field(None, description="Customer or business legal entity name")
    customer_email: Optional[str] = Field(None, description="Customer billing contact email")
    customer_phone: Optional[str] = Field(None, description="Customer billing contact phone")
    amount_paise: int = Field(..., gt=0, description="Total invoice amount in paise (e.g. 5000000 for ₹50,000)")
    paid_amount_paise: Optional[int] = Field(0, ge=0, description="Amount already paid towards this invoice in paise")
    currency: str = Field("INR", description="Three-letter currency code")
    due_at: datetime = Field(..., description="Invoice payment due date (ISO 8601)")
    status: str = Field("ISSUED", description="Event/Invoice status: INVOICE_CREATED, INVOICE_DUE, INVOICE_OVERDUE, INVOICE_PAID")
    occurred_at: Optional[datetime] = Field(None, description="When the business event occurred")
    source: str = Field("merchant_erp", description="Source system: merchant_erp, accounting, billing")


class ReceivableEventResponse(BaseModel):
    status: str
    event_id: str
    invoice_id: str
    internal_invoice_id: str
    event_type: str
    action_taken: str
    case_id: Optional[str] = None
    processed_at: datetime


class ReceivablesStatusResponse(BaseModel):
    connected: bool
    status_text: str
    invoice_count: int
    overdue_count: int
    paid_count: int
    last_event_at: Optional[datetime] = None
    supported_events: List[str] = [
        "INVOICE_CREATED",
        "INVOICE_DUE",
        "INVOICE_OVERDUE",
        "INVOICE_PAID"
    ]

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String


def generate_uuid(prefix: str = "") -> str:
    unique_id = uuid.uuid4().hex[:12]
    return f"{prefix}_{unique_id}" if prefix else unique_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

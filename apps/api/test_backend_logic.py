from app.database import SessionLocal
from app.api.v1.cases import create_manual_case
from app.schemas.recovery_case import ManualCaseRequest
from app.models.merchant import Merchant

db = SessionLocal()
merchant = db.query(Merchant).first()
if not merchant:
    print("No merchant found")
else:
    req = ManualCaseRequest(
        customer_name="Test Script",
        customer_email="test@test.com",
        customer_phone="1234567890",
        amount_paise=10000,
        promise_date="2026-10-10",
        notes="Test notes"
    )
    try:
        case_detail = create_manual_case(request=req, current_merchant=merchant, db=db)
        print("Success:", case_detail.id)
    except Exception as e:
        import traceback
        traceback.print_exc()

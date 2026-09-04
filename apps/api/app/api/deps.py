from typing import Optional
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.merchant import Merchant
from app.services.auth_service import decode_access_token

security = HTTPBearer(auto_error=False)


def get_current_merchant(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db)
) -> Merchant:
    """
    Extracts and validates current merchant tenant from Bearer token.
    In development mode, if no authorization header is provided, 
    falls back to the primary default seeded merchant.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate merchant credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if auth and auth.credentials:
        payload = decode_access_token(auth.credentials)
        if not payload:
            raise credentials_exception
        merchant_id: str = payload.get("sub")
        if not merchant_id:
            raise credentials_exception
        
        merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not merchant:
            raise credentials_exception
        return merchant

    # No fallback for unauthenticated users in production
    raise credentials_exception

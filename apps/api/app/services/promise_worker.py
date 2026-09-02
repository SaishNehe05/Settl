import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.promise import Promise
from app.services.recovery_service import analyze_case, execute_case_pipeline

logger = logging.getLogger(__name__)

def _process_overdue_promises():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # Find active promises that are past their promise date
        overdue_promises = (
            db.query(Promise)
            .filter(Promise.status == "ACTIVE", Promise.promise_date <= now)
            .all()
        )

        for promise in overdue_promises:
            logger.info(f"Promise {promise.id} for case {promise.case_id} is overdue.")
            
            # Transition promise to BROKEN
            promise.status = "BROKEN"
            promise.broken_at = now
            
            # Ensure we reset the case status if it was waiting on the promise
            if promise.recovery_case and promise.recovery_case.status == "READY":
                # We force it back to NEW or just let analyze_case reset it
                pass
                
            db.commit()
            
            # Re-evaluate AI & Policy
            analyze_case(db, promise.case_id)
            execute_case_pipeline(db, promise.case_id)
            
    except Exception as e:
        logger.error(f"Database error while processing overdue promises: {str(e)}")
        db.rollback()
    finally:
        db.close()

async def promise_lifecycle_worker():
    """
    Background worker that runs periodically to evaluate ACTIVE promises.
    """
    logger.info("Starting Promise lifecycle worker...")
    while True:
        try:
            # Wrap synchronous db operation
            await asyncio.to_thread(_process_overdue_promises)
        except asyncio.CancelledError:
            logger.info("Promise worker shutting down.")
            break
        except Exception as e:
            logger.error(f"Error in promise worker: {str(e)}")
        
        # Sleep for 60 seconds (for testing, normally this could be 5-10 minutes)
        await asyncio.sleep(60)

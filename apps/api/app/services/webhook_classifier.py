"""
Settl Webhook Event Classifier

Deterministic mapping between Razorpay provider event types and
Settl's internal event classification system.
"""
import logging

logger = logging.getLogger(__name__)

# ─── Razorpay event type → Settl event type ────────────────────────
RAZORPAY_TO_SETTL_MAP: dict[str, str] = {
    # Payment events
    "payment.failed":               "PAYMENT_FAILURE",
    "payment.authorized":           "PAYMENT_AUTHORIZED",
    "payment.captured":             "PAYMENT_SUCCESS",

    # Order events
    "order.paid":                   "ORDER_PAID",

    # Payment Link events (recovery verification)
    "payment_link.paid":            "RECOVERY_PAYMENT_SUCCESS",
    "payment_link.partially_paid":  "RECOVERY_PARTIAL_PAYMENT",
    "payment_link.cancelled":       "RECOVERY_LINK_CANCELLED",
    "payment_link.expired":         "RECOVERY_LINK_EXPIRED",

    # Subscription lifecycle
    "subscription.pending":         "SUBSCRIPTION_PENDING",
    "subscription.halted":          "SUBSCRIPTION_HALTED",
    "subscription.charged":         "SUBSCRIPTION_CHARGED",
    "subscription.activated":       "SUBSCRIPTION_ACTIVATED",
    "subscription.cancelled":       "SUBSCRIPTION_CANCELLED",
    "subscription.completed":       "SUBSCRIPTION_COMPLETED",
    "subscription.paused":          "SUBSCRIPTION_PAUSED",
    "subscription.resumed":         "SUBSCRIPTION_RESUMED",
}

# Events that indicate a revenue loss and should trigger case creation
REVENUE_LOSS_EVENTS: set[str] = {
    "PAYMENT_FAILURE",
    "SUBSCRIPTION_PENDING",
    "SUBSCRIPTION_HALTED",
}

# Events that can verify a recovery (payment received)
RECOVERY_VERIFICATION_EVENTS: set[str] = {
    "RECOVERY_PAYMENT_SUCCESS",
    "RECOVERY_PARTIAL_PAYMENT",
    "PAYMENT_SUCCESS",
    "ORDER_PAID",
    "SUBSCRIPTION_CHARGED",
    "SUBSCRIPTION_ACTIVATED",
}

# Events that are informational but do not trigger cases or recovery
INFORMATIONAL_EVENTS: set[str] = {
    "PAYMENT_AUTHORIZED",
    "RECOVERY_LINK_CANCELLED",
    "RECOVERY_LINK_EXPIRED",
    "SUBSCRIPTION_CANCELLED",
    "SUBSCRIPTION_COMPLETED",
    "SUBSCRIPTION_PAUSED",
    "SUBSCRIPTION_RESUMED",
}


def classify_event(razorpay_event_type: str) -> str:
    """
    Maps a Razorpay event type string to a Settl event classification.
    Returns 'UNHANDLED' for unknown event types.
    """
    settl_type = RAZORPAY_TO_SETTL_MAP.get(razorpay_event_type, "UNHANDLED")
    if settl_type == "UNHANDLED":
        logger.warning(f"Unhandled Razorpay event type: {razorpay_event_type}")
    return settl_type


def is_revenue_loss_event(settl_event_type: str) -> bool:
    """Returns True if this event type should trigger recovery case creation."""
    return settl_event_type in REVENUE_LOSS_EVENTS


def is_recovery_verification_event(settl_event_type: str) -> bool:
    """Returns True if this event type can verify that a recovery payment was received."""
    return settl_event_type in RECOVERY_VERIFICATION_EVENTS


def is_informational_event(settl_event_type: str) -> bool:
    """Returns True if this event is informational only (no case creation or recovery)."""
    return settl_event_type in INFORMATIONAL_EVENTS


def get_event_family(razorpay_event_type: str) -> str:
    """Returns the event family: 'payment', 'payment_link', 'subscription', 'order', or 'unknown'."""
    if razorpay_event_type.startswith("payment_link."):
        return "payment_link"
    elif razorpay_event_type.startswith("payment."):
        return "payment"
    elif razorpay_event_type.startswith("subscription."):
        return "subscription"
    elif razorpay_event_type.startswith("order."):
        return "order"
    return "unknown"

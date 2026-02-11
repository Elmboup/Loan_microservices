from __future__ import annotations

from libs.common.events import LOAN_DOCUMENTS_RECEIVED
from libs.common.rabbitmq import consume_events
from libs.common.logging import get_logger

from .worker import evaluate_property

logger = get_logger("property-consumer")

QUEUE_NAME = "property-service"


def handle_event(event: dict) -> None:
    loan_id = event.get("loan_id")
    payload = event.get("payload", {})
    insurance_interest = bool(payload.get("insurance_interest", False))
    logger.info("received %s for loan %s", event.get("event_type"), loan_id)
    evaluate_property.apply_async(args=[loan_id, insurance_interest], queue="property")


def start() -> None:
    consume_events(QUEUE_NAME, [LOAN_DOCUMENTS_RECEIVED], handle_event)

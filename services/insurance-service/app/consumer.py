from __future__ import annotations

from libs.common.events import DECISION_MADE
from libs.common.rabbitmq import consume_events
from libs.common.logging import get_logger

from .worker import generate_quote

logger = get_logger("insurance-consumer")

QUEUE_NAME = "insurance-service"


def handle_event(event: dict) -> None:
    loan_id = event.get("loan_id")
    payload = event.get("payload", {})
    eligible = bool(payload.get("eligible", False))
    insurance_interest = bool(payload.get("insurance_interest", False))
    logger.info("received decision for loan %s", loan_id)
    generate_quote.apply_async(args=[loan_id, eligible, insurance_interest], queue="insurance")


def start() -> None:
    consume_events(QUEUE_NAME, [DECISION_MADE], handle_event)

from __future__ import annotations

from libs.common.events import DECISION_MADE, INSURANCE_QUOTE_READY, LOAN_CREATED
from libs.common.rabbitmq import consume_events
from libs.common.logging import get_logger

from .store import store
from .worker import generate_insurance_quote

logger = get_logger("insurance-consumer")

QUEUE_NAME = "insurance-service"


def handle_event(event: dict) -> None:
    loan_id = event.get("loan_id")
    payload = event.get("payload", {})
    event_type = event.get("event_type")
    if not loan_id:
        logger.warning("received %s without loan_id", event_type)
        return

    if event_type == LOAN_CREATED:
        insurance_interest = bool(payload.get("insurance_interest", False))
        store.set_interest(loan_id, insurance_interest)
        logger.info("stored insurance interest=%s for loan %s", insurance_interest, loan_id)
        return

    if event_type == INSURANCE_QUOTE_READY:
        store.set_quote(loan_id, payload)
        logger.info("stored insurance quote for loan %s", loan_id)
        return

    if event_type == DECISION_MADE:
        eligible = bool(payload.get("eligible", False))
        insurance_interest = store.get_interest(loan_id)
        property_value = payload.get("property_value")
        if property_value is not None:
            try:
                property_value = int(property_value)
            except (TypeError, ValueError):
                property_value = None
        logger.info("received decision for loan %s", loan_id)
        if eligible and insurance_interest:
            generate_insurance_quote.apply_async(
                args=[loan_id, property_value],
                queue="insurance",
            )
        else:
            logger.info(
                "skip insurance quote for loan %s (eligible=%s, interest=%s)",
                loan_id,
                eligible,
                insurance_interest,
            )
        return

    logger.info("ignored event %s for loan %s", event_type, loan_id)


def start() -> None:
    consume_events(QUEUE_NAME, [LOAN_CREATED, DECISION_MADE, INSURANCE_QUOTE_READY], handle_event)

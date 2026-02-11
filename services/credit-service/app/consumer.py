from __future__ import annotations

from libs.common.events import CREDIT_COMPENSATE, LOAN_DOCUMENTS_RECEIVED
from libs.common.rabbitmq import consume_events
from libs.common.logging import get_logger

from .publisher import publish_credit_compensated
from .store import store
from .worker import check_credit

logger = get_logger("credit-consumer")

QUEUE_NAME = "credit-service"


def handle_event(event: dict) -> None:
    loan_id = event.get("loan_id")
    payload = event.get("payload", {})
    event_type = event.get("event_type")
    insurance_interest = bool(payload.get("insurance_interest", False))
    logger.info("received %s for loan %s", event_type, loan_id)

    if event_type == CREDIT_COMPENSATE:
        if store.is_compensated(loan_id):
            logger.info("credit already compensated for loan %s", loan_id)
            return
        store.set_compensated(loan_id, True)
        publish_credit_compensated(loan_id, {"status": "COMPENSATED"})
        logger.info("credit compensated for loan %s", loan_id)
        return

    check_credit.apply_async(args=[loan_id, insurance_interest], queue="credit")


def start() -> None:
    consume_events(QUEUE_NAME, [LOAN_DOCUMENTS_RECEIVED, CREDIT_COMPENSATE], handle_event)

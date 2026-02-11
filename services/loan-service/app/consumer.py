from __future__ import annotations

from uuid import uuid4

from libs.common.events import (
    ACCEPTANCE_PACKAGE_SENT,
    AGREEMENT_ACCEPTED,
    AGREEMENT_DECLINED,
    CREDIT_COMPENSATED,
    INSURANCE_QUOTE_READY,
    LOAN_APPROVED,
    LOAN_CANCELLED,
    LOAN_FINAL_APPROVED,
    LOAN_REJECTED,
)
from libs.common.logging import get_logger
from libs.common.rabbitmq import consume_events
from libs.common.schemas import LoanStatus

from .publisher import (
    publish_acceptance_package_sent,
    publish_loan_cancelled,
    publish_loan_final_approved,
)
from .store import store

logger = get_logger("loan-consumer")

QUEUE_NAME = "loan-service"


def _publish_acceptance_if_needed(loan_id: str) -> None:
    if store.get_acceptance_sent(loan_id):
        return
    schedule_id = str(uuid4())
    payload = {
        "repayment_schedule_id": schedule_id,
        "channel": "email",
        "insurance_included": store.get_insurance_included(loan_id),
    }
    publish_acceptance_package_sent(loan_id, payload)
    store.set_acceptance_sent(loan_id, True)


def _finalize_if_needed(loan_id: str, approved: bool) -> None:
    if store.get_finalized(loan_id):
        return
    if approved:
        publish_loan_final_approved(loan_id, {"status": "APPROVED"})
    else:
        publish_loan_cancelled(loan_id, {"status": "CANCELLED"})
    store.set_finalized(loan_id, True)


def handle_event(event: dict) -> None:
    loan_id = event.get("loan_id")
    payload = event.get("payload", {})
    event_type = event.get("event_type")
    if not loan_id:
        logger.warning("received %s without loan_id", event_type)
        return

    if store.get_finalized(loan_id) and event_type not in {LOAN_FINAL_APPROVED, LOAN_CANCELLED}:
        logger.info("ignore event %s for finalized loan %s", event_type, loan_id)
        return

    if event_type == INSURANCE_QUOTE_READY:
        store.set_insurance_included(loan_id, True)
        logger.info("insurance quote ready for loan %s", loan_id)
        return

    if event_type == LOAN_REJECTED:
        store.update_status(loan_id, LoanStatus.REJECTED)
        store.set_finalized(loan_id, True)
        logger.info("loan %s rejected", loan_id)
        return

    if event_type == LOAN_APPROVED:
        store.update_status(loan_id, LoanStatus.ACCEPTANCE_SENT)
        _publish_acceptance_if_needed(loan_id)
        store.update_status(loan_id, LoanStatus.AGREEMENT_PENDING)
        logger.info("loan %s approved (acceptance sent)", loan_id)
        return

    if event_type == ACCEPTANCE_PACKAGE_SENT:
        store.set_acceptance_sent(loan_id, True)
        store.update_status(loan_id, LoanStatus.AGREEMENT_PENDING)
        return

    if event_type in {AGREEMENT_ACCEPTED, AGREEMENT_DECLINED}:
        current = store.get(loan_id)
        if not current or current.status != LoanStatus.AGREEMENT_PENDING:
            logger.info("ignore agreement for loan %s (status=%s)", loan_id, current.status if current else None)
            return
        if event_type == AGREEMENT_ACCEPTED:
            store.update_status(loan_id, LoanStatus.APPROVED)
            _finalize_if_needed(loan_id, approved=True)
            logger.info("loan %s finally approved", loan_id)
        else:
            store.update_status(loan_id, LoanStatus.CANCELLED)
            _finalize_if_needed(loan_id, approved=False)
            logger.info("loan %s cancelled", loan_id)
        return

    if event_type in {LOAN_FINAL_APPROVED, LOAN_CANCELLED}:
        store.set_finalized(loan_id, True)
        return

    if event_type == CREDIT_COMPENSATED:
        logger.info("credit compensated for loan %s", loan_id)
        return

    logger.info("ignored event %s for loan %s", event_type, loan_id)


def start() -> None:
    consume_events(
        QUEUE_NAME,
        [
            LOAN_APPROVED,
            LOAN_REJECTED,
            ACCEPTANCE_PACKAGE_SENT,
            AGREEMENT_ACCEPTED,
            AGREEMENT_DECLINED,
            LOAN_CANCELLED,
            LOAN_FINAL_APPROVED,
            INSURANCE_QUOTE_READY,
            CREDIT_COMPENSATED,
        ],
        handle_event,
    )

from libs.common.events import (
    ACCEPTANCE_PACKAGE_SENT,
    EventEnvelope,
    LOAN_CANCELLED,
    LOAN_CREATED,
    LOAN_DOCS_RECEIVED,
    LOAN_DOCS_REQUESTED,
    LOAN_FINAL_APPROVED,
)
from libs.common.logging import get_logger
from libs.common.rabbitmq import publish_event

logger = get_logger("loan-publisher")


def publish_loan_created(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_CREATED, loan_id, payload)
    logger.info("published %s for loan %s", LOAN_CREATED, loan_id)
    publish_event(LOAN_CREATED, event.to_dict())


def publish_documents_requested(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_DOCS_REQUESTED, loan_id, payload)
    logger.info("published %s for loan %s", LOAN_DOCS_REQUESTED, loan_id)
    publish_event(LOAN_DOCS_REQUESTED, event.to_dict())


def publish_documents_received(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_DOCS_RECEIVED, loan_id, payload)
    logger.info("published %s for loan %s", LOAN_DOCS_RECEIVED, loan_id)
    publish_event(LOAN_DOCS_RECEIVED, event.to_dict())


def publish_acceptance_package_sent(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(ACCEPTANCE_PACKAGE_SENT, loan_id, payload)
    logger.info("published %s for loan %s", ACCEPTANCE_PACKAGE_SENT, loan_id)
    publish_event(ACCEPTANCE_PACKAGE_SENT, event.to_dict())


def publish_loan_final_approved(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_FINAL_APPROVED, loan_id, payload)
    logger.info("published %s for loan %s", LOAN_FINAL_APPROVED, loan_id)
    publish_event(LOAN_FINAL_APPROVED, event.to_dict())


def publish_loan_cancelled(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_CANCELLED, loan_id, payload)
    logger.info("published %s for loan %s", LOAN_CANCELLED, loan_id)
    publish_event(LOAN_CANCELLED, event.to_dict())

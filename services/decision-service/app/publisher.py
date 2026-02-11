from libs.common.events import CREDIT_COMPENSATE, DECISION_MADE, EventEnvelope, LOAN_APPROVED, LOAN_REJECTED
from libs.common.logging import get_logger
from libs.common.rabbitmq import publish_event

logger = get_logger("decision-publisher")


def publish_decision_made(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(DECISION_MADE, loan_id, payload)
    logger.info("published %s for loan %s", DECISION_MADE, loan_id)
    publish_event(DECISION_MADE, event.to_dict())


def publish_loan_approved(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_APPROVED, loan_id, payload)
    logger.info("published %s for loan %s", LOAN_APPROVED, loan_id)
    publish_event(LOAN_APPROVED, event.to_dict())


def publish_loan_rejected(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_REJECTED, loan_id, payload)
    logger.info("published %s for loan %s", LOAN_REJECTED, loan_id)
    publish_event(LOAN_REJECTED, event.to_dict())


def publish_credit_compensate(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(CREDIT_COMPENSATE, loan_id, payload)
    logger.info("published %s for loan %s", CREDIT_COMPENSATE, loan_id)
    publish_event(CREDIT_COMPENSATE, event.to_dict())

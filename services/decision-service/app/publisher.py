from libs.common.events import (
    DECISION_MADE,
    LOAN_APPROVED,
    LOAN_REJECTED,
    EventEnvelope,
)
from libs.common.rabbitmq import publish_event


def publish_decision_made(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(DECISION_MADE, loan_id, payload)
    publish_event(DECISION_MADE, event.to_dict())


def publish_loan_approved(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_APPROVED, loan_id, payload)
    publish_event(LOAN_APPROVED, event.to_dict())


def publish_loan_rejected(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_REJECTED, loan_id, payload)
    publish_event(LOAN_REJECTED, event.to_dict())

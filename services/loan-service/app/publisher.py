from libs.common.events import (
    EventEnvelope,
    LOAN_CREATED,
    LOAN_DOCUMENTS_RECEIVED,
    LOAN_DOCUMENTS_REQUESTED,
)
from libs.common.rabbitmq import publish_event


def publish_loan_created(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_CREATED, loan_id, payload)
    publish_event(LOAN_CREATED, event.to_dict())


def publish_documents_requested(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_DOCUMENTS_REQUESTED, loan_id, payload)
    publish_event(LOAN_DOCUMENTS_REQUESTED, event.to_dict())


def publish_documents_received(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(LOAN_DOCUMENTS_RECEIVED, loan_id, payload)
    publish_event(LOAN_DOCUMENTS_RECEIVED, event.to_dict())

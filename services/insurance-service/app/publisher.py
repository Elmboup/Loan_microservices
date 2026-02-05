from libs.common.events import EventEnvelope, INSURANCE_QUOTE_READY
from libs.common.rabbitmq import publish_event


def publish_quote_ready(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(INSURANCE_QUOTE_READY, loan_id, payload)
    publish_event(INSURANCE_QUOTE_READY, event.to_dict())

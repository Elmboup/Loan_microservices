from libs.common.events import EventEnvelope, PROPERTY_EVALUATED
from libs.common.rabbitmq import publish_event


def publish_property_evaluated(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(PROPERTY_EVALUATED, loan_id, payload)
    publish_event(PROPERTY_EVALUATED, event.to_dict())

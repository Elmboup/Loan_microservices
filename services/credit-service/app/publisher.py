from libs.common.events import CREDIT_CHECKED, EventEnvelope
from libs.common.rabbitmq import publish_event


def publish_credit_checked(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(CREDIT_CHECKED, loan_id, payload)
    publish_event(CREDIT_CHECKED, event.to_dict())

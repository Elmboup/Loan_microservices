from libs.common.events import CREDIT_CHECKED, CREDIT_COMPENSATED, EventEnvelope
from libs.common.rabbitmq import publish_event


def publish_credit_checked(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(CREDIT_CHECKED, loan_id, payload)
    publish_event(CREDIT_CHECKED, event.to_dict())


def publish_credit_compensated(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(CREDIT_COMPENSATED, loan_id, payload)
    publish_event(CREDIT_COMPENSATED, event.to_dict())

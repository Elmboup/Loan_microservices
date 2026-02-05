from libs.common.events import AGREEMENT_ACCEPTED, AGREEMENT_DECLINED, EventEnvelope
from libs.common.rabbitmq import publish_event


def publish_agreement_accepted(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(AGREEMENT_ACCEPTED, loan_id, payload)
    publish_event(AGREEMENT_ACCEPTED, event.to_dict())


def publish_agreement_declined(loan_id: str, payload: dict) -> None:
    event = EventEnvelope.create(AGREEMENT_DECLINED, loan_id, payload)
    publish_event(AGREEMENT_DECLINED, event.to_dict())

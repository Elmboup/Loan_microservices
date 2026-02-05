from __future__ import annotations

from libs.common.events import CREDIT_CHECKED, PROPERTY_EVALUATED
from libs.common.rabbitmq import consume_events
from libs.common.logging import get_logger

from .config import DECISION_MIN_CREDIT, DECISION_MIN_PROPERTY
from .publisher import publish_decision_made, publish_loan_approved, publish_loan_rejected
from .store import store

logger = get_logger("decision-consumer")

QUEUE_NAME = "decision-service"


def _try_decide(loan_id: str) -> None:
    if store.get_decision(loan_id):
        return

    credit = store.get_credit(loan_id)
    prop = store.get_property(loan_id)
    if not credit or not prop:
        return

    eligible = credit["credit_score"] >= DECISION_MIN_CREDIT and prop["property_value"] >= DECISION_MIN_PROPERTY
    reason = None if eligible else "criteria not met"

    decision_payload = {
        "eligible": eligible,
        "credit_score": credit["credit_score"],
        "property_value": prop["property_value"],
        "insurance_interest": credit.get("insurance_interest", False) or prop.get("insurance_interest", False),
        "reason": reason,
    }

    store.set_decision(loan_id, decision_payload)
    publish_decision_made(loan_id, decision_payload)
    if eligible:
        publish_loan_approved(loan_id, {"reason": "approved"})
    else:
        publish_loan_rejected(loan_id, {"reason": reason})


def handle_event(event: dict) -> None:
    loan_id = event.get("loan_id")
    payload = event.get("payload", {})
    event_type = event.get("event_type")
    logger.info("received %s for loan %s", event_type, loan_id)

    if event_type == CREDIT_CHECKED:
        store.set_credit(loan_id, payload)
    elif event_type == PROPERTY_EVALUATED:
        store.set_property(loan_id, payload)

    _try_decide(loan_id)


def start() -> None:
    consume_events(QUEUE_NAME, [CREDIT_CHECKED, PROPERTY_EVALUATED], handle_event)

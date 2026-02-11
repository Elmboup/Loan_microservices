from __future__ import annotations

from libs.common.events import CREDIT_CHECKED, PROPERTY_EVALUATED
from libs.common.logging import get_logger
from libs.common.rabbitmq import consume_events
from .publisher import (
    publish_credit_compensate,
    publish_decision_made,
    publish_loan_approved,
    publish_loan_rejected,
)
from .store import store

logger = get_logger("decision-consumer")

QUEUE_NAME = "decision-service"

MIN_CREDIT_SCORE = 600
MIN_PROPERTY_VALUE = 100000


def compute_eligibility(credit_payload: dict, property_payload: dict) -> tuple[bool, str, dict]:
    credit_ok = credit_payload.get("credit_ok")
    if credit_ok is None:
        credit_ok = True
    credit_ok = bool(credit_ok)

    property_ok = property_payload.get("property_ok")
    if property_ok is None:
        property_ok = True
    property_ok = bool(property_ok)
    credit_score = int(credit_payload.get("credit_score") or 0)
    property_value = int(property_payload.get("property_value") or 0)

    if not credit_ok:
        reason = "CREDIT_FAILED"
        eligible = False
    elif not property_ok:
        reason = "PROPERTY_FAILED"
        eligible = False
    elif credit_score < MIN_CREDIT_SCORE or property_value < MIN_PROPERTY_VALUE:
        reason = "THRESHOLD_NOT_MET"
        eligible = False
    else:
        reason = "ELIGIBLE"
        eligible = True

    decision_details = {
        "eligible": eligible,
        "reason": reason,
        "credit_score": credit_score,
        "property_value": property_value,
    }
    return eligible, reason, decision_details


def _try_decide(loan_id: str) -> None:
    if store.get_decision(loan_id):
        return

    credit = store.get_credit(loan_id)
    prop = store.get_property(loan_id)
    if not credit or not prop:
        return

    eligible, reason, decision_payload = compute_eligibility(credit, prop)
    logger.info("decision computed for loan %s eligible=%s reason=%s", loan_id, eligible, reason)

    store.set_decision(loan_id, decision_payload)
    publish_decision_made(loan_id, decision_payload)
    if eligible:
        publish_loan_approved(
            loan_id,
            {
                "eligible": True,
                "reason": reason,
                "credit_score": decision_payload["credit_score"],
                "property_value": decision_payload["property_value"],
            },
        )
    else:
        publish_loan_rejected(
            loan_id,
            {
                "eligible": False,
                "reason": reason,
                "credit_score": decision_payload["credit_score"],
                "property_value": decision_payload["property_value"],
            },
        )
        if reason == "PROPERTY_FAILED":
            publish_credit_compensate(
                loan_id,
                {
                    "reason": reason,
                    "correlation_event_id": store.get_property_event_id(loan_id),
                },
            )


def handle_event(event: dict) -> None:
    loan_id = event.get("loan_id")
    payload = event.get("payload", {})
    event_type = event.get("event_type")
    if not loan_id:
        logger.warning("received %s without loan_id", event_type)
        return
    logger.info("received %s for loan %s", event_type, loan_id)

    if event_type == CREDIT_CHECKED:
        store.set_credit(loan_id, payload, event.get("event_id"))
    elif event_type == PROPERTY_EVALUATED:
        store.set_property(loan_id, payload, event.get("event_id"))

    _try_decide(loan_id)


def start() -> None:
    consume_events(QUEUE_NAME, [CREDIT_CHECKED, PROPERTY_EVALUATED], handle_event)

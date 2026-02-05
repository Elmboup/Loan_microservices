from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

# Exchange name is configured via env, but routing keys are constants here.

LOAN_CREATED = "loan.created"
LOAN_DOCUMENTS_RECEIVED = "loan.documents.received"
LOAN_DOCUMENTS_REQUESTED = "loan.documents.requested"

CREDIT_CHECKED = "credit.checked"
PROPERTY_EVALUATED = "property.evaluated"
DECISION_MADE = "decision.made"
LOAN_APPROVED = "loan.approved"
LOAN_REJECTED = "loan.rejected"
INSURANCE_QUOTE_READY = "insurance.quote.ready"
AGREEMENT_ACCEPTED = "agreement.accepted"
AGREEMENT_DECLINED = "agreement.declined"

ALL_ROUTING_KEYS = [
    LOAN_CREATED,
    LOAN_DOCUMENTS_RECEIVED,
    LOAN_DOCUMENTS_REQUESTED,
    CREDIT_CHECKED,
    PROPERTY_EVALUATED,
    DECISION_MADE,
    LOAN_APPROVED,
    LOAN_REJECTED,
    INSURANCE_QUOTE_READY,
    AGREEMENT_ACCEPTED,
    AGREEMENT_DECLINED,
]


@dataclass
class EventEnvelope:
    event_id: str
    event_type: str
    timestamp: str
    loan_id: str
    payload: dict

    @staticmethod
    def create(event_type: str, loan_id: str, payload: dict) -> "EventEnvelope":
        return EventEnvelope(
            event_id=str(uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            loan_id=loan_id,
            payload=payload,
        )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "loan_id": self.loan_id,
            "payload": self.payload,
        }

from __future__ import annotations

import threading
from typing import Dict, List, Optional


class NotificationStore:
    def __init__(self, max_latest: int = 100) -> None:
        self._lock = threading.Lock()
        self._events_by_loan: Dict[str, List[dict]] = {}
        self._latest_events: List[dict] = []
        self._status_by_loan: Dict[str, str] = {}
        self._max_latest = max_latest

    def _derive_status(self, event: dict) -> Optional[str]:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        if event_type == "loan.created":
            return "CREATED"
        if event_type == "loan.documents.requested":
            return "DOCS_REQUESTED"
        if event_type == "loan.documents.received":
            return "DOCS_RECEIVED"
        if event_type == "decision.made":
            eligible = bool(payload.get("eligible", False))
            return "ELIGIBLE" if eligible else "NOT_ELIGIBLE"
        if event_type == "acceptance.package.sent":
            return "AGREEMENT_PENDING"
        if event_type == "agreement.accepted":
            return "APPROVED"
        if event_type in {"agreement.declined", "loan.cancelled"}:
            return "CANCELLED"
        if event_type == "loan.rejected":
            return "REJECTED"
        if event_type == "loan.final.approved":
            return "APPROVED"
        return None

    def add_event(self, event: dict) -> None:
        loan_id = event.get("loan_id")
        with self._lock:
            self._latest_events.append(event)
            if len(self._latest_events) > self._max_latest:
                self._latest_events = self._latest_events[-self._max_latest :]

            if loan_id:
                self._events_by_loan.setdefault(loan_id, []).append(event)
                status = self._derive_status(event)
                if status:
                    self._status_by_loan[loan_id] = status

    def list_loans(self) -> List[dict]:
        with self._lock:
            return [
                {"loan_id": loan_id, "status": self._status_by_loan.get(loan_id)}
                for loan_id in sorted(self._events_by_loan.keys())
            ]

    def get_events(self, loan_id: str) -> List[dict]:
        with self._lock:
            return list(self._events_by_loan.get(loan_id, []))

    def get_latest(self) -> List[dict]:
        with self._lock:
            return list(self._latest_events)

    def get_status(self, loan_id: str) -> Optional[str]:
        with self._lock:
            return self._status_by_loan.get(loan_id)


store = NotificationStore()

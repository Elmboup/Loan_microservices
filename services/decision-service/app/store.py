from __future__ import annotations

from typing import Dict


class DecisionStore:
    def __init__(self) -> None:
        self._store: Dict[str, dict] = {}

    def _ensure(self, loan_id: str) -> dict:
        entry = self._store.get(loan_id)
        if not entry:
            entry = {
                "credit": None,
                "credit_event_id": None,
                "property": None,
                "property_event_id": None,
                "decision": None,
            }
            self._store[loan_id] = entry
        return entry

    def set_credit(self, loan_id: str, result: dict, event_id: str | None = None) -> None:
        entry = self._ensure(loan_id)
        entry["credit"] = result
        entry["credit_event_id"] = event_id

    def set_property(self, loan_id: str, result: dict, event_id: str | None = None) -> None:
        entry = self._ensure(loan_id)
        entry["property"] = result
        entry["property_event_id"] = event_id

    def set_decision(self, loan_id: str, decision: dict) -> None:
        entry = self._ensure(loan_id)
        entry["decision"] = decision

    def get_credit(self, loan_id: str) -> dict | None:
        entry = self._store.get(loan_id)
        return entry["credit"] if entry else None

    def get_property(self, loan_id: str) -> dict | None:
        entry = self._store.get(loan_id)
        return entry["property"] if entry else None

    def get_credit_event_id(self, loan_id: str) -> str | None:
        entry = self._store.get(loan_id)
        return entry["credit_event_id"] if entry else None

    def get_property_event_id(self, loan_id: str) -> str | None:
        entry = self._store.get(loan_id)
        return entry["property_event_id"] if entry else None

    def get_decision(self, loan_id: str) -> dict | None:
        entry = self._store.get(loan_id)
        return entry["decision"] if entry else None

    def get_state(self, loan_id: str) -> dict | None:
        return self._store.get(loan_id)

    def list_ids(self) -> list[str]:
        return list(self._store.keys())


store = DecisionStore()

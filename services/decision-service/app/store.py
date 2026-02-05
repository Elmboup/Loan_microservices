from __future__ import annotations

from typing import Dict


class DecisionStore:
    def __init__(self) -> None:
        self.credit_results: Dict[str, dict] = {}
        self.property_results: Dict[str, dict] = {}
        self.decisions: Dict[str, dict] = {}

    def set_credit(self, loan_id: str, result: dict) -> None:
        self.credit_results[loan_id] = result

    def set_property(self, loan_id: str, result: dict) -> None:
        self.property_results[loan_id] = result

    def get_credit(self, loan_id: str) -> dict | None:
        return self.credit_results.get(loan_id)

    def get_property(self, loan_id: str) -> dict | None:
        return self.property_results.get(loan_id)

    def get_decision(self, loan_id: str) -> dict | None:
        return self.decisions.get(loan_id)

    def set_decision(self, loan_id: str, decision: dict) -> None:
        self.decisions[loan_id] = decision


store = DecisionStore()

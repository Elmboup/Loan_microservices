from __future__ import annotations

from typing import Dict


class InsuranceStore:
    def __init__(self) -> None:
        self._interest_by_loan: Dict[str, bool] = {}
        self._quotes_by_loan: Dict[str, dict] = {}

    def set_interest(self, loan_id: str, interest: bool) -> None:
        self._interest_by_loan[loan_id] = bool(interest)

    def get_interest(self, loan_id: str) -> bool:
        return bool(self._interest_by_loan.get(loan_id, False))

    def set_quote(self, loan_id: str, quote: dict) -> None:
        self._quotes_by_loan[loan_id] = quote

    def get_quote(self, loan_id: str) -> dict | None:
        return self._quotes_by_loan.get(loan_id)

    def get_state(self, loan_id: str) -> dict | None:
        if loan_id not in self._interest_by_loan and loan_id not in self._quotes_by_loan:
            return None
        return {
            "loan_id": loan_id,
            "insurance_interest": self._interest_by_loan.get(loan_id),
            "quote": self._quotes_by_loan.get(loan_id),
        }

    def list_quotes(self) -> list[dict]:
        return [
            {"loan_id": loan_id, "quote": quote}
            for loan_id, quote in self._quotes_by_loan.items()
        ]


store = InsuranceStore()

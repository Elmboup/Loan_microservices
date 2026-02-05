from __future__ import annotations

from typing import Dict

from libs.common.schemas import Loan


class LoanStore:
    def __init__(self) -> None:
        self._loans: Dict[str, Loan] = {}

    def add(self, loan: Loan) -> None:
        self._loans[loan.loan_id] = loan

    def get(self, loan_id: str) -> Loan | None:
        return self._loans.get(loan_id)

    def update_status(self, loan_id: str, status: str) -> None:
        loan = self._loans.get(loan_id)
        if loan:
            loan.status = status


store = LoanStore()

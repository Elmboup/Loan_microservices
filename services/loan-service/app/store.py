from __future__ import annotations

from typing import Dict, List, Optional

from libs.common.schemas import LoanDetail, LoanStatus

REQUIRED_DOCUMENTS = ["id", "income_proof", "property_docs"]


def compute_missing_documents(documents: Optional[dict]) -> List[str]:
    existing = set(documents or {})
    return [doc for doc in REQUIRED_DOCUMENTS if doc not in existing]


class LoanStore:
    def __init__(self) -> None:
        self._loans: Dict[str, LoanDetail] = {}
        self._acceptance_sent: Dict[str, bool] = {}
        self._finalized: Dict[str, bool] = {}
        self._insurance_included: Dict[str, bool] = {}

    def add(self, loan: LoanDetail) -> None:
        self._loans[loan.loan_id] = loan

    def get(self, loan_id: str) -> LoanDetail | None:
        return self._loans.get(loan_id)

    def update_status(self, loan_id: str, status: LoanStatus) -> None:
        loan = self._loans.get(loan_id)
        if loan:
            loan.status = status

    def set_acceptance_sent(self, loan_id: str, sent: bool) -> None:
        self._acceptance_sent[loan_id] = bool(sent)

    def get_acceptance_sent(self, loan_id: str) -> bool:
        return bool(self._acceptance_sent.get(loan_id, False))

    def set_finalized(self, loan_id: str, finalized: bool) -> None:
        self._finalized[loan_id] = bool(finalized)

    def get_finalized(self, loan_id: str) -> bool:
        return bool(self._finalized.get(loan_id, False))

    def set_insurance_included(self, loan_id: str, included: bool) -> None:
        self._insurance_included[loan_id] = bool(included)

    def get_insurance_included(self, loan_id: str) -> bool:
        return bool(self._insurance_included.get(loan_id, False))


store = LoanStore()

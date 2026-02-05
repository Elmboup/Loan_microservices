from __future__ import annotations

from typing import Dict


class AgreementStore:
    def __init__(self) -> None:
        self._agreements: Dict[str, str] = {}

    def set(self, loan_id: str, status: str) -> None:
        self._agreements[loan_id] = status

    def get(self, loan_id: str) -> str | None:
        return self._agreements.get(loan_id)


store = AgreementStore()

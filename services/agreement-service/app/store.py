from __future__ import annotations

from typing import Dict


class AgreementStore:
    def __init__(self) -> None:
        self._agreements: Dict[str, dict] = {}

    def set(self, loan_id: str, agreement: dict) -> None:
        self._agreements[loan_id] = agreement

    def get(self, loan_id: str) -> dict | None:
        return self._agreements.get(loan_id)


store = AgreementStore()

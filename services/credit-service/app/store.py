from __future__ import annotations

from typing import Dict


class CreditStore:
    def __init__(self) -> None:
        self._compensated: Dict[str, bool] = {}

    def set_compensated(self, loan_id: str, compensated: bool) -> None:
        self._compensated[loan_id] = bool(compensated)

    def is_compensated(self, loan_id: str) -> bool:
        return bool(self._compensated.get(loan_id, False))


store = CreditStore()

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class LoanCreate(BaseModel):
    applicant_name: str
    amount: float = Field(gt=0)
    property_address: str
    insurance_interest: bool = False


class Loan(BaseModel):
    loan_id: str
    applicant_name: str
    amount: float
    property_address: str
    insurance_interest: bool
    status: str = "created"


class CreditResult(BaseModel):
    loan_id: str
    credit_score: int


class PropertyResult(BaseModel):
    loan_id: str
    property_value: int


class Decision(BaseModel):
    loan_id: str
    eligible: bool
    reason: Optional[str] = None

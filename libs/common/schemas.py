from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class LoanStatus(str, Enum):
    CREATED = "CREATED"
    DOCS_REQUESTED = "DOCS_REQUESTED"
    DOCS_RECEIVED = "DOCS_RECEIVED"
    EVALUATING = "EVALUATING"
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    ACCEPTANCE_SENT = "ACCEPTANCE_SENT"
    AGREEMENT_PENDING = "AGREEMENT_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LoanCreate(BaseModel):
    client_id: str
    insurance_interest: bool = False
    documents: Optional[Dict[str, Any]] = None


class LoanDocuments(BaseModel):
    documents: Dict[str, Any]


class LoanSummary(BaseModel):
    loan_id: str
    status: LoanStatus
    missing_documents: List[str]


class LoanDetail(BaseModel):
    loan_id: str
    client_id: str
    insurance_interest: bool
    documents: Dict[str, Any]
    status: LoanStatus
    missing_documents: List[str]


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

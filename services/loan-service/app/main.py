from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException

from libs.common.logging import get_logger
from libs.common.schemas import Loan, LoanCreate

from .publisher import (
    publish_documents_received,
    publish_documents_requested,
    publish_loan_created,
)
from .store import store

logger = get_logger("loan-service")

app = FastAPI(title="loan-service")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/loans", response_model=Loan)
def create_loan(data: LoanCreate) -> Loan:
    loan_id = str(uuid4())
    loan = Loan(loan_id=loan_id, **data.model_dump())
    store.add(loan)

    publish_loan_created(loan_id, data.model_dump())
    publish_documents_requested(loan_id, {"message": "please provide documents"})

    return loan


@app.post("/loans/{loan_id}/documents")
def upload_documents(loan_id: str) -> dict:
    loan = store.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="loan not found")

    store.update_status(loan_id, "documents_received")
    publish_documents_received(loan_id, {"message": "documents received"})
    return {"status": "ok"}


@app.get("/loans/{loan_id}", response_model=Loan)
def get_loan(loan_id: str) -> Loan:
    loan = store.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="loan not found")
    return loan

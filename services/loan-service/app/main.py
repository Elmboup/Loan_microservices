from __future__ import annotations

import threading
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response

from libs.common.logging import get_logger
from libs.common.metrics import render_metrics
from libs.common.schemas import LoanCreate, LoanDetail, LoanDocuments, LoanStatus, LoanSummary

from .consumer import start
from .publisher import (
    publish_documents_received,
    publish_documents_requested,
    publish_loan_created,
)
from .store import compute_missing_documents, store

logger = get_logger("loan-service")

app = FastAPI(title="loan-service")


@app.on_event("startup")
def startup() -> None:
    thread = threading.Thread(target=start, daemon=True)
    thread.start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/loans", response_model=LoanSummary)
def create_loan(data: LoanCreate) -> LoanSummary:
    loan_id = str(uuid4())
    documents = data.documents or {}
    missing_documents = compute_missing_documents(documents)
    loan = LoanDetail(
        loan_id=loan_id,
        client_id=data.client_id,
        insurance_interest=data.insurance_interest,
        documents=documents,
        status=LoanStatus.CREATED,
        missing_documents=[],
    )
    store.add(loan)

    publish_loan_created(
        loan_id,
        {"client_id": data.client_id, "insurance_interest": data.insurance_interest},
    )
    status = LoanStatus.DOCS_REQUESTED if missing_documents else LoanStatus.DOCS_RECEIVED
    loan.status = status
    loan.missing_documents = missing_documents

    if missing_documents:
        publish_documents_requested(loan_id, {"missing_documents": missing_documents})
    else:
        publish_documents_received(
            loan_id,
            {
                "documents_summary": {"provided": list(documents.keys())},
                "insurance_interest": data.insurance_interest,
            },
        )

    return LoanSummary(loan_id=loan_id, status=status, missing_documents=missing_documents)


@app.post("/loans/{loan_id}/documents", response_model=LoanSummary)
def upload_documents(loan_id: str, data: LoanDocuments) -> LoanSummary:
    loan = store.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="loan not found")

    previous_missing = list(loan.missing_documents)
    previous_status = loan.status

    merged_documents = {**loan.documents, **data.documents}
    missing_documents = compute_missing_documents(merged_documents)
    status = LoanStatus.DOCS_RECEIVED if not missing_documents else LoanStatus.DOCS_REQUESTED

    loan.documents = merged_documents
    loan.missing_documents = missing_documents
    loan.status = status

    should_publish = (missing_documents != previous_missing) or (status != previous_status)
    if should_publish:
        if status == LoanStatus.DOCS_RECEIVED:
            publish_documents_received(
                loan_id,
                {
                    "documents_summary": {"provided": list(merged_documents.keys())},
                    "insurance_interest": loan.insurance_interest,
                },
            )
        else:
            publish_documents_requested(loan_id, {"missing_documents": missing_documents})

    return LoanSummary(loan_id=loan_id, status=status, missing_documents=missing_documents)


@app.get("/loans/{loan_id}", response_model=LoanDetail)
def get_loan(loan_id: str) -> LoanDetail:
    loan = store.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="loan not found")
    return loan


@app.get("/metrics")
def metrics() -> Response:
    return Response(render_metrics(), media_type="text/plain")

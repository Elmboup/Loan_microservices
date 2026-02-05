from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from libs.common.logging import get_logger

from .publisher import publish_agreement_accepted, publish_agreement_declined
from .store import store

logger = get_logger("agreement-service")

app = FastAPI(title="agreement-service")


class AgreementRequest(BaseModel):
    accepted: bool


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/loans/{loan_id}/agreement")
def submit_agreement(loan_id: str, data: AgreementRequest) -> dict:
    if data.accepted:
        store.set(loan_id, "accepted")
        publish_agreement_accepted(loan_id, {"status": "accepted"})
        return {"status": "accepted"}

    store.set(loan_id, "declined")
    publish_agreement_declined(loan_id, {"status": "declined"})
    raise HTTPException(status_code=400, detail="agreement declined")

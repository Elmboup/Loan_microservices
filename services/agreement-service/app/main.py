from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

from libs.common.logging import get_logger
from libs.common.metrics import render_metrics

from .publisher import (
    publish_agreement_accepted,
    publish_agreement_declined,
    publish_agreement_received,
)
from .store import store

logger = get_logger("agreement-service")

app = FastAPI(title="agreement-service")


class AgreementRequest(BaseModel):
    accepted: bool
    comment: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/loans/{loan_id}/agreement")
def submit_agreement(loan_id: str, data: AgreementRequest) -> dict:
    existing = store.get(loan_id)
    if existing:
        if existing.get("accepted") != data.accepted:
            raise HTTPException(status_code=409, detail="agreement already recorded")
        return {"loan_id": loan_id, "accepted": existing["accepted"], "status": "RECORDED"}

    signed_at = datetime.now(timezone.utc).isoformat()
    agreement = {
        "loan_id": loan_id,
        "accepted": data.accepted,
        "comment": data.comment,
        "signed_at": signed_at,
    }
    store.set(loan_id, agreement)

    publish_agreement_received(loan_id, {"accepted": data.accepted, "comment": data.comment})
    payload = {"accepted": data.accepted, "comment": data.comment, "signed_at": signed_at}
    if data.accepted:
        publish_agreement_accepted(loan_id, payload)
    else:
        publish_agreement_declined(loan_id, payload)

    return {"loan_id": loan_id, "accepted": data.accepted, "status": "RECORDED"}


@app.get("/loans/{loan_id}/agreement")
def get_agreement(loan_id: str) -> dict:
    agreement = store.get(loan_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="agreement not found")
    return agreement


@app.get("/metrics")
def metrics() -> Response:
    return Response(render_metrics(), media_type="text/plain")

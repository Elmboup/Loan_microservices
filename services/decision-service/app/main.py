from __future__ import annotations

import threading

from fastapi import FastAPI, HTTPException, Response

from libs.common.logging import get_logger
from libs.common.metrics import render_metrics

from .consumer import start
from .store import store

logger = get_logger("decision-service")

app = FastAPI(title="decision-service")


@app.on_event("startup")
def startup() -> None:
    thread = threading.Thread(target=start, daemon=True)
    thread.start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/decisions/{loan_id}")
def get_decision(loan_id: str) -> dict:
    decision = store.get_state(loan_id)
    if not decision:
        raise HTTPException(status_code=404, detail="decision not found")
    return decision


@app.get("/decisions")
def list_decisions() -> list[str]:
    return store.list_ids()


@app.get("/metrics")
def metrics() -> Response:
    return Response(render_metrics(), media_type="text/plain")

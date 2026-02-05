from __future__ import annotations

import threading

from fastapi import FastAPI, HTTPException

from libs.common.logging import get_logger

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
    decision = store.get_decision(loan_id)
    if not decision:
        raise HTTPException(status_code=404, detail="decision not found")
    return decision

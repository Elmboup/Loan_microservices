from __future__ import annotations

import threading

from fastapi import FastAPI, HTTPException, Response

from libs.common.logging import get_logger
from libs.common.metrics import render_metrics

from .consumer import start
from .store import store

logger = get_logger("insurance-service")

app = FastAPI(title="insurance-service")


@app.on_event("startup")
def startup() -> None:
    thread = threading.Thread(target=start, daemon=True)
    thread.start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/insurance/{loan_id}")
def get_insurance(loan_id: str) -> dict:
    state = store.get_state(loan_id)
    if not state:
        raise HTTPException(status_code=404, detail="insurance not found")
    return state


@app.get("/insurance")
def list_insurance() -> list[dict]:
    return store.list_quotes()


@app.get("/metrics")
def metrics() -> Response:
    return Response(render_metrics(), media_type="text/plain")

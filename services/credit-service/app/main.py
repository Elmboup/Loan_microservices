from __future__ import annotations

import threading

from fastapi import FastAPI, Response

from libs.common.logging import get_logger
from libs.common.metrics import render_metrics

from .consumer import start

logger = get_logger("credit-service")

app = FastAPI(title="credit-service")


@app.on_event("startup")
def startup() -> None:
    thread = threading.Thread(target=start, daemon=True)
    thread.start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/debug")
def debug() -> dict:
    return {"service": "credit-service"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(render_metrics(), media_type="text/plain")

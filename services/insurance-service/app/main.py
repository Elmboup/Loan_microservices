from __future__ import annotations

import threading

from fastapi import FastAPI

from libs.common.logging import get_logger

from .consumer import start

logger = get_logger("insurance-service")

app = FastAPI(title="insurance-service")


@app.on_event("startup")
def startup() -> None:
    thread = threading.Thread(target=start, daemon=True)
    thread.start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

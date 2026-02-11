from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path

from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from libs.common.logging import get_logger
from libs.common.metrics import render_metrics

from .consumer import start
from .hub import Hub
from .store import store

logger = get_logger("notification-service")

app = FastAPI(title="notification-service")

hub = Hub()


@app.on_event("startup")
async def startup() -> None:
    loop = asyncio.get_running_loop()
    thread = threading.Thread(target=start, args=(hub, loop), daemon=True)
    thread.start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def dashboard() -> Response:
    html_path = Path(__file__).parent / "templates" / "index.html"
    html = html_path.read_text(encoding="utf-8")
    return Response(html, media_type="text/html")


@app.get("/metrics")
def metrics() -> Response:
    return Response(render_metrics(), media_type="text/plain")


@app.get("/events")
async def sse_events():
    queue = await hub.register_sse()

    async def event_generator():
        try:
            while True:
                message = await queue.get()
                data = json.dumps(message)
                yield f"data: {data}\n\n"
        finally:
            hub.unregister_sse(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/loans")
def list_loans() -> list[dict]:
    return store.list_loans()


@app.get("/loans/{loan_id}/events")
def loan_events(loan_id: str) -> list[dict]:
    return store.get_events(loan_id)


@app.websocket("/ws/{loan_id}")
async def ws_events(websocket: WebSocket, loan_id: str):
    await websocket.accept()
    await hub.register_ws(loan_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.unregister_ws(loan_id, websocket)

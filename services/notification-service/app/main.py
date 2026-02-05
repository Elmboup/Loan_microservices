from __future__ import annotations

import asyncio
import json
import threading

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from libs.common.logging import get_logger

from .consumer import start
from .hub import Hub

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


@app.websocket("/ws/{loan_id}")
async def ws_events(websocket: WebSocket, loan_id: str):
    await websocket.accept()
    await hub.register_ws(loan_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.unregister_ws(loan_id, websocket)

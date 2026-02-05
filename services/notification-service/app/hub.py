from __future__ import annotations

import asyncio
from typing import Dict, List


class Hub:
    def __init__(self) -> None:
        self._sse_clients: List[asyncio.Queue] = []
        self._ws_clients: Dict[str, List] = {}

    async def register_sse(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._sse_clients.append(queue)
        return queue

    def unregister_sse(self, queue: asyncio.Queue) -> None:
        if queue in self._sse_clients:
            self._sse_clients.remove(queue)

    async def register_ws(self, loan_id: str, ws) -> None:
        self._ws_clients.setdefault(loan_id, []).append(ws)

    def unregister_ws(self, loan_id: str, ws) -> None:
        if loan_id in self._ws_clients and ws in self._ws_clients[loan_id]:
            self._ws_clients[loan_id].remove(ws)
            if not self._ws_clients[loan_id]:
                del self._ws_clients[loan_id]

    async def broadcast(self, message: dict) -> None:
        for queue in list(self._sse_clients):
            await queue.put(message)

        loan_id = message.get("loan_id")
        if loan_id in self._ws_clients:
            for ws in list(self._ws_clients[loan_id]):
                await ws.send_json(message)

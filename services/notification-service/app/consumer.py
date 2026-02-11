from __future__ import annotations

import asyncio

from libs.common.events import ALL_ROUTING_KEYS
from libs.common.rabbitmq import consume_events
from libs.common.logging import get_logger

from .hub import Hub
from .store import store

logger = get_logger("notification-consumer")

QUEUE_NAME = "notification-service"


def start(hub: Hub, loop: asyncio.AbstractEventLoop) -> None:
    def handle_event(event: dict) -> None:
        store.add_event(event)
        logger.info("consumed event_type=%s loan_id=%s", event.get("event_type"), event.get("loan_id"))
        asyncio.run_coroutine_threadsafe(hub.broadcast(event), loop)

    consume_events(QUEUE_NAME, ["#"], handle_event)

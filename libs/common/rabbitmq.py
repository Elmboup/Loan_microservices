from __future__ import annotations

import json
import os
import time
from typing import Callable, Dict

import pika
from pika.adapters.blocking_connection import BlockingChannel

from .logging import get_logger
from .metrics import inc_metric

logger = get_logger("rabbitmq")

DLX_EXCHANGE = "events.dlx"
DEFAULT_MAX_ATTEMPTS = 3


def _connection_params() -> pika.ConnectionParameters:
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASS", "guest")
    vhost = os.getenv("RABBITMQ_VHOST", "/")
    credentials = pika.PlainCredentials(user, password)
    return pika.ConnectionParameters(host=host, port=port, virtual_host=vhost, credentials=credentials)


def get_exchange() -> str:
    return os.getenv("RABBITMQ_EXCHANGE", "events")


def _max_attempts() -> int:
    try:
        return int(os.getenv("RABBITMQ_MAX_ATTEMPTS", str(DEFAULT_MAX_ATTEMPTS)))
    except ValueError:
        return DEFAULT_MAX_ATTEMPTS


def _declare_exchanges(channel: BlockingChannel) -> None:
    exchange = get_exchange()
    channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
    channel.exchange_declare(exchange=DLX_EXCHANGE, exchange_type="direct", durable=True)


def _declare_queue_with_dlq(channel: BlockingChannel, queue_name: str) -> None:
    dlq_queue = f"{queue_name}.dlq"
    dlq_routing_key = f"{queue_name}.dlq"
    args = {
        "x-dead-letter-exchange": DLX_EXCHANGE,
        "x-dead-letter-routing-key": dlq_routing_key,
    }
    channel.queue_declare(queue=queue_name, durable=True, arguments=args)
    channel.queue_declare(queue=dlq_queue, durable=True)
    channel.queue_bind(queue=dlq_queue, exchange=DLX_EXCHANGE, routing_key=dlq_routing_key)


def publish_event(routing_key: str, message: dict) -> None:
    connection = pika.BlockingConnection(_connection_params())
    channel: BlockingChannel = connection.channel()
    exchange = get_exchange()
    _declare_exchanges(channel)
    event = dict(message)
    attempt = int(event.get("attempt") or 0)
    event["attempt"] = attempt
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(event).encode("utf-8"),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            headers={"x-attempt": attempt},
        ),
    )
    logger.info(
        "event_published event_type=%s loan_id=%s event_id=%s attempt=%s",
        event.get("event_type"),
        event.get("loan_id"),
        event.get("event_id"),
        attempt,
    )
    inc_metric("events_published_total")
    connection.close()


def consume_events(queue_name: str, routing_keys: list[str], handler: Callable[[dict], None]) -> None:
    while True:
        try:
            connection = pika.BlockingConnection(_connection_params())
            channel: BlockingChannel = connection.channel()
            exchange = get_exchange()
            _declare_exchanges(channel)
            _declare_queue_with_dlq(channel, queue_name)
            for key in routing_keys:
                channel.queue_bind(queue=queue_name, exchange=exchange, routing_key=key)

            def _on_message(ch, method, properties, body):
                payload: dict | None = None
                try:
                    payload = json.loads(body.decode("utf-8"))
                    handler(payload)
                    logger.info(
                        "event_consumed event_type=%s loan_id=%s event_id=%s attempt=%s",
                        payload.get("event_type"),
                        payload.get("loan_id"),
                        payload.get("event_id"),
                        payload.get("attempt", 0),
                    )
                    inc_metric("events_consumed_total")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("handler error: %s", exc)
                    attempt = 0
                    if payload is None:
                        logger.error("event_dlq event_type=%s loan_id=%s attempt=%s", None, None, attempt)
                        inc_metric("dlq_total")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                        return
                    if isinstance(payload, Dict):
                        try:
                            attempt = int(payload.get("attempt") or 0)
                        except (TypeError, ValueError):
                            attempt = 0
                    max_attempts = _max_attempts()
                    if attempt < max_attempts:
                        retry_payload = dict(payload or {})
                        retry_payload["attempt"] = attempt + 1
                        publish_event(method.routing_key, retry_payload)
                        logger.warning(
                            "event_retry event_type=%s loan_id=%s attempt=%s",
                            retry_payload.get("event_type"),
                            retry_payload.get("loan_id"),
                            retry_payload.get("attempt"),
                        )
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        logger.error(
                            "event_dlq event_type=%s loan_id=%s attempt=%s",
                            payload.get("event_type") if isinstance(payload, Dict) else None,
                            payload.get("loan_id") if isinstance(payload, Dict) else None,
                            attempt,
                        )
                        inc_metric("dlq_total")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=_on_message)
            channel.start_consuming()
        except Exception as exc:  # noqa: BLE001
            logger.exception("consumer connection error: %s", exc)
            time.sleep(2)

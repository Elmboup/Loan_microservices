from __future__ import annotations

import json
import os
import time
from typing import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel

from .logging import get_logger

logger = get_logger("rabbitmq")


def _connection_params() -> pika.ConnectionParameters:
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASS", "guest")
    vhost = os.getenv("RABBITMQ_VHOST", "/")
    credentials = pika.PlainCredentials(user, password)
    return pika.ConnectionParameters(host=host, port=port, virtual_host=vhost, credentials=credentials)


def get_exchange() -> str:
    return os.getenv("RABBITMQ_EXCHANGE", "loan.events")


def publish_event(routing_key: str, message: dict) -> None:
    connection = pika.BlockingConnection(_connection_params())
    channel: BlockingChannel = connection.channel()
    exchange = get_exchange()
    channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(message).encode("utf-8"),
        properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
    )
    connection.close()


def consume_events(queue_name: str, routing_keys: list[str], handler: Callable[[dict], None]) -> None:
    while True:
        try:
            connection = pika.BlockingConnection(_connection_params())
            channel: BlockingChannel = connection.channel()
            exchange = get_exchange()
            channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
            channel.queue_declare(queue=queue_name, durable=True)
            for key in routing_keys:
                channel.queue_bind(queue=queue_name, exchange=exchange, routing_key=key)

            def _on_message(ch, method, properties, body):
                try:
                    payload = json.loads(body.decode("utf-8"))
                    handler(payload)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("handler error: %s", exc)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=_on_message)
            channel.start_consuming()
        except Exception as exc:  # noqa: BLE001
            logger.exception("consumer connection error: %s", exc)
            time.sleep(2)

from __future__ import annotations

import random
import time
from celery import Celery
from kombu import Queue

from libs.common.logging import get_logger

from .config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from .publisher import publish_quote_ready

logger = get_logger("insurance-worker")

celery_app = Celery("insurance-service", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.task_queues = [Queue("insurance")]
celery_app.conf.task_default_queue = "insurance"


@celery_app.task(name="generate_insurance_quote")
def generate_insurance_quote(loan_id: str, property_value: int | None = None) -> dict:
    time.sleep(random.randint(2, 5))
    if property_value is None:
        quote_amount = 15000
    else:
        quote_amount = int(property_value * 0.0025)
    payload = {
        "quote_amount": quote_amount,
        "currency": "XOF",
        "provider": "MockAssureur",
        "eligible": True,
    }
    publish_quote_ready(loan_id, payload)
    logger.info("insurance quote ready for %s", loan_id)
    return payload

from __future__ import annotations

import time
from celery import Celery

from libs.common.logging import get_logger

from .config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from .publisher import publish_quote_ready

logger = get_logger("insurance-worker")

celery_app = Celery("insurance-service", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


@celery_app.task(name="generate_quote")
def generate_quote(loan_id: str, eligible: bool, insurance_interest: bool) -> dict:
    time.sleep(1)
    if not eligible or not insurance_interest:
        return {"skipped": True}
    quote = 200 + (abs(hash(loan_id)) % 300)
    payload = {"quote": quote}
    publish_quote_ready(loan_id, payload)
    logger.info("insurance quote ready for %s", loan_id)
    return payload

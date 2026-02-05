from __future__ import annotations

import time
from celery import Celery

from libs.common.logging import get_logger

from .config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from .publisher import publish_property_evaluated

logger = get_logger("property-worker")

celery_app = Celery("property-service", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


@celery_app.task(name="evaluate_property")
def evaluate_property(loan_id: str, insurance_interest: bool = False) -> dict:
    time.sleep(2)
    value = 80000 + (abs(hash(loan_id)) % 200000)
    payload = {"property_value": value, "insurance_interest": insurance_interest}
    publish_property_evaluated(loan_id, payload)
    logger.info("property evaluated for %s", loan_id)
    return payload

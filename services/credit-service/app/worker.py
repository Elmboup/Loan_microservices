from __future__ import annotations

import time
from celery import Celery

from libs.common.logging import get_logger

from .config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from .publisher import publish_credit_checked

logger = get_logger("credit-worker")

celery_app = Celery("credit-service", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


@celery_app.task(name="check_credit")
def check_credit(loan_id: str, insurance_interest: bool = False) -> dict:
    time.sleep(2)
    score = 500 + (abs(hash(loan_id)) % 300)
    payload = {"credit_score": score, "insurance_interest": insurance_interest}
    publish_credit_checked(loan_id, payload)
    logger.info("credit checked for %s", loan_id)
    return payload

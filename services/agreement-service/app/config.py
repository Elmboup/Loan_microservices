import os

RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "loan.events")

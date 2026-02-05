FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY services/loan-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY libs /app/libs
COPY services/loan-service/app /app/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim

RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY worker/ /app/worker/

RUN mkdir -p /app/data && chown appuser:appuser /app/data

ENV PYTHONPATH=/app

USER appuser

CMD ["python", "-m", "worker.app.main"]

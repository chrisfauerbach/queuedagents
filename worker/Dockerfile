FROM python:3.12-slim

WORKDIR /app

COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY worker/ /app/worker/

ENV PYTHONPATH=/app

CMD ["python", "-m", "worker.app.main"]

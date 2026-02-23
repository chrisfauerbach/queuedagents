FROM python:3.12-slim

RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY gpu-monitor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY gpu-monitor/ /app/gpu_monitor/

RUN mkdir -p /app/data && chown appuser:appuser /app/data

ENV PYTHONPATH=/app

USER appuser

CMD ["python", "-m", "gpu_monitor.app.main"]

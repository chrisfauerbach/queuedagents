FROM python:3.12-slim

WORKDIR /app

COPY gpu-monitor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY gpu-monitor/ /app/gpu_monitor/

ENV PYTHONPATH=/app

CMD ["python", "-m", "gpu_monitor.app.main"]

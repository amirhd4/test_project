FROM python:3.12-slim

WORKDIR /app

# Prevent Python from writing .pyc files & buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/notification_service

ENV PYTHONPATH=/app

CMD ["uvicorn", "notification_service.app.main:app", "--host", "0.0.0.0", "--port", "8001"]

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

EXPOSE 8000
# Host is env-driven: defaults to :: for Railway (IPv6-only private networking), but local
# docker-compose sets UVICORN_HOST=0.0.0.0 so IPv4 curl/healthchecks work. Shell form so the
# env var expands.
CMD uvicorn app.main:app --host "${UVICORN_HOST:-::}" --port 8000

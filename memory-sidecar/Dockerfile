FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Bake the local embedding model into the image so the first request isn't slow and the
# container needs no internet to embed (extraction still calls the 0G router).
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"

COPY app ./app

EXPOSE 3002
# Host is env-driven: defaults to :: for Railway (IPv6-only private networking); local
# docker-compose sets UVICORN_HOST=0.0.0.0. Shell form so the env var expands.
CMD uvicorn app.main:app --host "${UVICORN_HOST:-::}" --port 3002

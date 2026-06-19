FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

EXPOSE 8000
# Bind IPv6 (::) — Railway private networking is IPv6-only, so other services reach
# this at backend.railway.internal:8000. uvicorn on :: also accepts IPv4-mapped clients.
CMD ["uvicorn", "app.main:app", "--host", "::", "--port", "8000"]

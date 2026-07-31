FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY models/ ./models/

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 5050

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050", "--workers", "2"]
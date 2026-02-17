# syntax=docker/dockerfile:1
# HIGH SECURITY FIX: Use specific version tags instead of floating tags
FROM python:3.12.1-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# runtime
# HIGH SECURITY FIX: Use specific version tag
FROM python:3.12.1-slim-bookworm

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY . .

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

USER appuser

# HIGH SECURITY FIX: Proper healthcheck for blockchain service
# Checks if scheduler is running (not just sys.exit(0))
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os; os.path.exists('/tmp/.healthy') or exit(1)"

CMD ["python", "main.py"]

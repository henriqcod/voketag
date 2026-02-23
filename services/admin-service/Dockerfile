# Python Admin Service

FROM python:3.11-slim

WORKDIR /app

# Install dependencies (global, so appuser can use them)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make sure scripts are in PATH
ENV PYTHONPATH=/app

# Run as non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')" || exit 1

# Expose port
EXPOSE 8080

# Run migrations, create initial admin if env set, then application
CMD ["sh", "-c", "alembic upgrade head && (if [ -n \"$INIT_ADMIN_EMAIL\" ]; then python -m admin_service.scripts.create_admin \"$INIT_ADMIN_EMAIL\" \"$INIT_ADMIN_PASSWORD\" \"${INIT_ADMIN_NAME:-Admin}\" --super-admin 2>/dev/null || true; fi) && python -m uvicorn admin_service.main:app --host 0.0.0.0 --port 8080"]

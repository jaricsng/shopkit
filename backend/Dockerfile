# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install runtime deps from the HASH-LOCKED lockfile first — reproducible builds
# (every dep pinned + sha256-verified) and a cacheable layer. Regenerate with:
#   pip-compile --generate-hashes -o requirements.txt pyproject.toml
COPY requirements.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# Then install the app package itself without re-resolving deps.
COPY . .
RUN pip install --no-cache-dir --no-deps .

# Run as a non-root user (matches the kit's minimal-service Dockerfile).
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# /health is the liveness probe; /ready (checks the DB) is the readiness probe.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

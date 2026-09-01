# ==============================================================================
# Stage 1: Builder stage — Install dependencies using uv
# ==============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Prevent Python from writing .pyc files & buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv (ultra-fast Python package installer)
RUN pip install --no-cache-dir uv

# Copy package management files
COPY pyproject.toml .

# Install production dependencies into the system site-packages
RUN uv pip install --system --no-cache -r pyproject.toml

# ==============================================================================
# Stage 2: Final Runtime Stage — Lightweight execution environment
# ==============================================================================
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///./feedback.db
ENV LOG_LEVEL=INFO

# Copy installed site-packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy backend application source code
COPY . .

# Expose FastAPI server port
EXPOSE 8000

# Health check endpoint for container orchestrators (App Service / ACI / Kubernetes)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start FastAPI application using Uvicorn
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim AS base

# Prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for psycopg binary and lxml
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || true

# Copy source code
COPY src/ src/
COPY scripts/ scripts/

# Install the package
RUN pip install --no-cache-dir -e .

# Create data directories
RUN mkdir -p data/raw data/exports data/backups

# Default command: show help
CMD ["scrapper", "--help"]

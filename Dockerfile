# Multi-stage build for improved security and smaller image size

# Build stage - installs dependencies in a temporary image
# Use the latest digest for the slim image (Replace <PASTE_DIGEST_HERE> with the actual digest found using 'docker inspect')
FROM python:3.11-slim@sha256:<PASTE_DIGEST_HERE> AS builder

WORKDIR /app

# Install build dependencies if needed for any Python packages with C extensions
# Also install curl needed for healthcheck in the final stage (copying it is complex)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Final stage - clean image with only what's needed
# Use the latest digest for the slim image (Replace <PASTE_DIGEST_HERE> with the actual digest found using 'docker inspect')
# IMPORTANT: Ensure this digest matches the one used in the builder stage
FROM python:3.11-slim@sha256:<PASTE_DIGEST_HERE>

# Install curl needed for healthcheck (must be installed in final stage)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create a non-root user and group
RUN groupadd -r appuser && \
    useradd --no-log-init -r -g appuser appuser && \
    mkdir -p /home/appuser && \
    chown -R appuser:appuser /home/appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appuser . .

# Set proper permissions
RUN chmod -R 755 /app

# Switch to the non-root user
USER appuser

# Expose the port
EXPOSE 8000

# Health check
# Ensure curl is installed in this stage
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

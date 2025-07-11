# --- Build Stage ---
# Use a temporary build stage to install dependencies
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build-time system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install them into the virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- Final Stage ---
# Use a clean, new slim image for the final product
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime system dependencies (curl for the healthcheck)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port (Google Cloud Run uses PORT env var)
EXPOSE 8080

# Health check (assumes you have a /docs endpoint like FastAPI provides)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/docs || exit 1

# Run the application using the production version
# CMD ["python", "run_prod.py"]

# Run the application using the production server directly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
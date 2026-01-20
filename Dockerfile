# Stationery Shop SaaS - Dockerfile
# Multi-stage build for Python/Django

FROM python:3.13-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create and set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Final stage
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN addgroup --system app && adduser --system --group app

# Set work directory
WORKDIR $APP_HOME

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --clear || true

# Change ownership to app user
RUN chown -R app:app $APP_HOME

# Switch to app user
USER app

# Expose port
EXPOSE 8000

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

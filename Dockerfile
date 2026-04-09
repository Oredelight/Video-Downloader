# Build stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/app/.venv/bin:$PATH"

# Install system dependencies required for yt-dlp and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python -m venv .venv && \
    .venv/bin/pip install --upgrade pip && \
    .venv/bin/pip install -r requirements.txt

# Copy project
COPY . .

# Create directories for media and static files
RUN mkdir -p /app/media /app/staticfiles

# Collect static files (before dropping privileges)
RUN python manage.py collectstatic --noinput --clear || true

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Create entrypoint script
RUN echo '#!/bin/bash\n\
python manage.py migrate --noinput || true\n\
python manage.py collectstatic --noinput --clear || true\n\
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --threads 2 --worker-class gthread --timeout 120 --access-logfile - --error-logfile - videodownloader.wsgi:application' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

# Run gunicorn with entrypoint
CMD ["/app/entrypoint.sh"]

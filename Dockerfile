# Use Python 3.12 alpine image (smaller and more secure)
FROM python:3.12-alpine3.20

# Set working directory
WORKDIR /app

# Install system dependencies (Alpine uses apk instead of apt-get)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user (Alpine uses adduser instead of useradd)
RUN adduser -D -s /bin/sh app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "main:app"]

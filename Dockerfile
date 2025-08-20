# Use Python 3.12 alpine image (smaller and more secure)
FROM python:3.12-alpine3.20

# Set working directory
WORKDIR /app

# Install system dependencies (Alpine uses apk instead of apt-get)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    nginx \
    certbot \
    certbot-nginx \
    openssl \
    dcron

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Make start script executable
RUN chmod +x start.sh

# Create non-root user and set up nginx directories as root
RUN adduser -D -s /bin/sh app \
    && chown -R app:app /app \
    && mkdir -p /run/nginx \
    && mkdir -p /var/log/nginx \
    && mkdir -p /etc/letsencrypt \
    && mkdir -p /var/lib/letsencrypt \
    && mkdir -p /var/log/letsencrypt \
    && chmod 755 /run/nginx \
    && chmod 755 /var/log/nginx \
    && chmod 755 /etc/letsencrypt \
    && chmod 755 /var/lib/letsencrypt

# Expose ports (HTTP and HTTPS)
EXPOSE 80 443

# Health check (check nginx instead of gunicorn directly)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:80/health || exit 1

# Run both nginx and gunicorn
CMD ["./start.sh"]

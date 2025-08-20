#!/bin/sh

echo "Starting Barbs with delayed SSL setup..."

# Start Gunicorn as app user in the background
echo "Starting Gunicorn..."
su app -c "gunicorn --bind 127.0.0.1:8000 --workers 3 main:app" &

# Wait for Gunicorn to start
sleep 3

# Start with HTTP-only nginx configuration
cat > /etc/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    upstream app {
        server 127.0.0.1:8000;
    }
    
    server {
        listen 80;
        server_name search.barbsdogrescue.org;
        
        # Let's Encrypt challenge location
        location /.well-known/acme-challenge/ {
            root /var/lib/letsencrypt/;
        }
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        
        # Static files - served directly by nginx
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Proxy everything else to Gunicorn
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Start SSL setup in background
echo "Starting SSL setup process in background..."
/app/ssl-setup.sh > /var/log/ssl-setup.log 2>&1 &

# Start nginx in the foreground
echo "Starting Nginx (HTTP initially, SSL will be added automatically)..."
exec nginx -g "daemon off;"

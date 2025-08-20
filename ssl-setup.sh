#!/bin/sh

# Wait for HTTP to be working
echo "Waiting for HTTP service to be available..."
while ! wget --quiet --tries=1 --spider http://localhost:80/health; do
    sleep 5
done

echo "HTTP service is up, waiting for DNS propagation..."
sleep 60  # Give DNS time to propagate

echo "Attempting SSL certificate generation..."
certbot certonly \
    --webroot \
    --webroot-path=/var/lib/letsencrypt \
    --email charlie@barbsdogrescue.org \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d search.barbsdogrescue.org

if [ $? -eq 0 ]; then
    echo "SSL certificate obtained successfully!"
    echo "Updating nginx configuration for SSL..."
    
    # Create SSL-enabled nginx config
    cat > /etc/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    upstream app {
        server 127.0.0.1:8000;
    }
    
    # HTTP server - redirects to HTTPS and handles Let's Encrypt challenges
    server {
        listen 80;
        server_name search.barbsdogrescue.org;
        
        # Let's Encrypt challenge location
        location /.well-known/acme-challenge/ {
            root /var/lib/letsencrypt/;
        }
        
        # Health check endpoint (keep available on HTTP)
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
        
        # Redirect all other HTTP traffic to HTTPS
        location / {
            return 301 https://$server_name$request_uri;
        }
    }
    
    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name search.barbsdogrescue.org;
        
        # SSL configuration
        ssl_certificate /etc/letsencrypt/live/search.barbsdogrescue.org/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/search.barbsdogrescue.org/privkey.pem;
        
        # SSL security settings
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=63072000" always;
        
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
            proxy_set_header X-Forwarded-Proto https;
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
    
    # Reload nginx with SSL configuration
    nginx -s reload
    
    # Set up automatic renewal
    echo "0 */12 * * * /usr/bin/certbot renew --quiet && /usr/sbin/nginx -s reload" > /etc/crontabs/root
    crond -b -S
    
    echo "HTTPS is now active!"
else
    echo "SSL certificate generation failed, staying with HTTP only"
fi

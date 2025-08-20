#!/bin/sh

echo "Starting Barbs with SSL support..."

# Function to obtain SSL certificate
obtain_ssl_cert() {
    echo "Obtaining SSL certificate for search.barbsdogrescue.org..."
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
        return 0
    else
        echo "Failed to obtain SSL certificate"
        return 1
    fi
}

# Function to check if SSL certificate exists and is valid
check_ssl_cert() {
    if [ -f "/etc/letsencrypt/live/search.barbsdogrescue.org/fullchain.pem" ]; then
        # Check if certificate expires in more than 30 days
        if openssl x509 -checkend 2592000 -noout -in /etc/letsencrypt/live/search.barbsdogrescue.org/fullchain.pem; then
            echo "Valid SSL certificate found"
            return 0
        else
            echo "SSL certificate expires soon, will renew"
            return 1
        fi
    else
        echo "No SSL certificate found"
        return 1
    fi
}

# Start Gunicorn as app user in the background
echo "Starting Gunicorn..."
su app -c "gunicorn --bind 127.0.0.1:8000 --workers 3 main:app" &

# Wait for Gunicorn to start
sleep 3

# Start nginx temporarily on HTTP only for certificate generation
echo "Starting Nginx (HTTP only) for certificate generation..."
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.ssl
cat > /etc/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    upstream app {
        server 127.0.0.1:8000;
    }
    
    server {
        listen 80;
        server_name search.barbsdogrescue.org;
        
        location /.well-known/acme-challenge/ {
            root /var/lib/letsencrypt/;
        }
        
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
        
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Start nginx in background for certificate generation
nginx &
NGINX_PID=$!
sleep 2

# Check if we need to obtain a certificate
if ! check_ssl_cert; then
    echo "Obtaining SSL certificate..."
    if obtain_ssl_cert; then
        echo "SSL certificate obtained successfully"
        # Stop nginx
        kill $NGINX_PID 2>/dev/null || true
        wait $NGINX_PID 2>/dev/null || true
        
        # Restore SSL-enabled nginx config
        mv /etc/nginx/nginx.conf.ssl /etc/nginx/nginx.conf
        
        # Set up automatic renewal (check twice daily)
        echo "0 */12 * * * /usr/bin/certbot renew --quiet && /usr/sbin/nginx -s reload" > /etc/crontabs/root
        
        # Start crond for automatic renewal
        crond -b -S
        
        # Start nginx with SSL in the foreground
        echo "Starting Nginx with SSL..."
        exec nginx -g "daemon off;"
    else
        echo "Warning: Could not obtain SSL certificate, continuing with HTTP only"
        # The nginx is already running for HTTP, just wait for it
        echo "Continuing with HTTP-only configuration..."
        wait $NGINX_PID
    fi
else
    echo "Using existing SSL certificate"
    # Stop nginx
    kill $NGINX_PID 2>/dev/null || true
    wait $NGINX_PID 2>/dev/null || true
    
    # Restore SSL-enabled nginx config
    mv /etc/nginx/nginx.conf.ssl /etc/nginx/nginx.conf
    
    # Set up automatic renewal (check twice daily)
    echo "0 */12 * * * /usr/bin/certbot renew --quiet && /usr/sbin/nginx -s reload" > /etc/crontabs/root
    
    # Start crond for automatic renewal
    crond -b -S
    
    # Start nginx with SSL in the foreground
    echo "Starting Nginx with SSL..."
    exec nginx -g "daemon off;"
fi

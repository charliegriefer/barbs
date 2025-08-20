#!/bin/sh

# Start Gunicorn as app user in the background
echo "Starting Gunicorn..."
su app -c "gunicorn --bind 127.0.0.1:8000 --workers 3 main:app" &

# Wait a moment for Gunicorn to start
sleep 2

# Start nginx as root in the foreground
echo "Starting Nginx..."
exec nginx -g "daemon off;"

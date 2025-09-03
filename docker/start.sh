#!/bin/sh

echo "Starting Gunicorn..."
gunicorn -w 3 -b 127.0.0.1:8000 main:app &

echo "Starting Nginx..."
nginx -g "daemon off;"
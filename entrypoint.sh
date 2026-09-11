#!/bin/bash
set -e

echo "[INFO] Running initial save file parse..."
python3 parse.py

echo "[INFO] Starting Nginx web server..."
exec nginx -g 'daemon off;'

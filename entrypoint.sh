#!/bin/sh
set -e

echo "[INFO] Starting Stardew Save Analyzer..."
echo "[INFO] Scanning save directory and generating dashboard..."

START_TIME=$(date +%s%3N 2>/dev/null || date +%s)

# Execute Python parser
python3 parse.py

END_TIME=$(date +%s%3N 2>/dev/null || date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo "[OK] Dashboard generation finished in ${ELAPSED}ms."
echo "[INFO] Initializing Nginx web server on port 80..."
echo "[OK] Initialization complete. Stardew Save Analyzer is ready and listening for incoming HTTP requests!"

# Hand execution over to Nginx in foreground
exec nginx -g 'daemon off;'

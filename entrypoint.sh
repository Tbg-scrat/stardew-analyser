#!/bin/sh
set -e

echo "[] Parsing Stardew Save File..."
python3 parse.py

echo "[ðŸš] Starting Nginx Server..."
exec nginx -g 'daemon off;'

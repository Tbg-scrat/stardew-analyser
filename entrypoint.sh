#!/bin/bash
set -e

echo "[INFO] Starting Nginx web server..."
nginx

echo "[INFO] Launching save file watcher..."
exec python3 watch.py


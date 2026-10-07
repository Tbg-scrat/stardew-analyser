#!/bin/bash
set -e

echo "[INFO] Verifying game asset cache..."
python3 -m src.core.asset_extractor || echo "[WARN] Asset extraction step skipped or encountered non-fatal error."

echo "[INFO] Starting Nginx web server..."
nginx

echo "[INFO] Launching save file watcher..."
exec python3 watch.py


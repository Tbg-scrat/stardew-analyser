#!/bin/bash
set -e

echo "[INFO] Verifying game asset cache via dynamic router..."
# Changed from src.core.asset_extractor to src.core.extractor.router
python3 -m src.core.extractor.router || echo "[WARN] Asset extraction step skipped or encountered non-fatal error."

echo "[INFO] Starting Nginx web server..."
nginx

echo "[INFO] Launching save file watcher..."
exec python3 watch.py


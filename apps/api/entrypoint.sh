#!/bin/sh
set -e

mkdir -p storage/local_uploads storage/local_queue

echo "[entrypoint] Starting uvicorn..."
exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

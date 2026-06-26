#!/bin/sh
set -e
mkdir -p storage/local_uploads storage/local_queue 2>/dev/null || true
exec "$@"

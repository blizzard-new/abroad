#!/bin/sh
# A separate CGU edition with disposable storage. Never run against production data.
set -eu
exec uvicorn exchange_info.cgu_demo:create_demo_app --factory \
  --host "${CGU_DEMO_HOST:-127.0.0.1}" --port "${PORT:-8000}" \
  --workers 1 --no-proxy-headers

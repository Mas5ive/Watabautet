#!/usr/bin/env bash

set -e
set -x

# Create and clean up a folder for Prometheus multi-process metrics
rm -rf /tmp/prometheus_multiproc_dir
mkdir -p /tmp/prometheus_multiproc_dir

alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
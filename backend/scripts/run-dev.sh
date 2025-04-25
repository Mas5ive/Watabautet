#!/usr/bin/env bash

set -e
set -x

bash scripts/migration.sh

exec python3 -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 \
    -m uvicorn app.main:app --host 0.0.0.0 --reload
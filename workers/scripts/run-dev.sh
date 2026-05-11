#!/usr/bin/env bash

set -e
set -x

exec watchmedo auto-restart \
  --directory=. \
  --pattern="*.py" \
  --recursive \
  -- \
  python3 -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5679 \
  -m celery -A app worker --uid=nobody --gid=nogroup

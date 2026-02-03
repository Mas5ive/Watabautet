#!/usr/bin/env bash

set -e
set -x

alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
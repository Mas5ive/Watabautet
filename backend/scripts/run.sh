#!/usr/bin/env bash

set -e
set -x

alembic upgrade head

exec uvicorn app.main:app --workers 4
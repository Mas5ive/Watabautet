#!/usr/bin/env bash

set -e
set -x

bash scripts/migration.sh

exec uvicorn app.main:app --workers 4
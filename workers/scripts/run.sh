#!/usr/bin/env bash

set -e
set -x

exec celery -A app worker

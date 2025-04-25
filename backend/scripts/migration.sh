#!/bin/bash

set -e

if [[ $(alembic current | wc -l) -eq 0 ]]; then
  echo "No applied migrations detected, running upgrade."
  alembic upgrade head
else
  echo "Applied migrations detected, skipping upgrade."
fi
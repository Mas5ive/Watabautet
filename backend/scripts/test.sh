#!/usr/bin/env bash

set -e
set -x

bash scripts/migration.sh

if [ "$DEBUG" = "true" ]; then
  echo "Debugger enabled. Waiting for client to connect to 0.0.0.0:5680..."
  DEBUGGER_CMD="python3 -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5680 --wait-for-client"
  COMMAND_TO_EXEC="$DEBUGGER_CMD -m pytest"
else
  COMMAND_TO_EXEC="python3 -m pytest"
fi

exec $COMMAND_TO_EXEC "$@"
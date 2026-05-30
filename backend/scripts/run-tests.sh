#!/usr/bin/env bash

set -e
set -x 

COMPOSE_FILE="docker-compose.test.yml"
ENV_FILE="../.env"

cleanup() {
  echo "Cleaning up containers..."
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans
}

trap cleanup EXIT

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend bash scripts/test.sh "$@"
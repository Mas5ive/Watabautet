#!/usr/bin/env bash

set -x

uv run ruff check app/ --fix
uv run autopep8 -air app/
#!/usr/bin/env bash

set -e
set -x

uv run pyright app/
uv run ruff check app/
uv run autopep8 -dar app/
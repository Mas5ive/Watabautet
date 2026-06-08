FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/workers/.venv/bin:$PATH"

WORKDIR /workers


FROM base AS builder

COPY --from=ghcr.io/astral-sh/uv:0.7.5 /uv /uvx /bin/

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=workers/uv.lock,target=uv.lock \
    --mount=type=bind,source=workers/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project


FROM builder AS dev

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=workers/uv.lock,target=uv.lock \
    --mount=type=bind,source=workers/pyproject.toml,target=pyproject.toml \
    uv sync --locked --group dev --no-install-project

COPY ./workers/uv.lock ./workers/pyproject.toml /workers/
COPY ./workers/scripts ./scripts
COPY ./workers/app ./app


FROM base AS prod

COPY --from=builder /workers/.venv /workers/.venv
COPY ./workers/uv.lock ./workers/pyproject.toml /workers/
COPY ./workers/scripts ./scripts
COPY ./workers/app ./app

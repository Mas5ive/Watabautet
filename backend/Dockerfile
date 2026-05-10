FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1

WORKDIR /backend

COPY --from=ghcr.io/astral-sh/uv:0.7.5 /uv /uvx /bin/

ENV UV_LINK_MODE=copy
ENV PATH="/backend/.venv/bin:$PATH"

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/uv.lock,target=uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev

COPY ./backend/uv.lock ./backend/pyproject.toml ./backend/alembic.ini /backend/
COPY ./backend/scripts ./scripts
COPY ./backend/app ./app


FROM base AS prod

ENV LOG_ENV=prod


FROM base AS dev

ENV LOG_ENV=dev

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --group dev

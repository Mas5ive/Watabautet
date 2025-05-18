FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1

WORKDIR /backend

COPY --from=ghcr.io/astral-sh/uv:0.7.5 /uv /uvx /bin/

ENV UV_LINK_MODE=copy
ENV PATH="/backend/.venv/bin:$PATH"

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-default-groups
    
COPY ./backend/app ./app
COPY ./backend/scripts ./scripts
COPY ./uv.lock ./backend/pyproject.toml ./backend/alembic.ini /backend/



FROM base AS dev

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --group dev



FROM base AS test

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --group test



FROM base AS dev-test

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --all-groups

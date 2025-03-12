FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1

WORKDIR /workers

COPY --from=ghcr.io/astral-sh/uv:0.5.2 /uv /uvx /bin/

ENV UV_LINK_MODE=copy
ENV PATH="/workers/.venv/bin:$PATH"

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=workers/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

COPY ./workers/app ./app
COPY ./workers/scripts ./scripts
COPY ./uv.lock ./workers/pyproject.toml /workers/



FROM base AS dev

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

CMD ["watchmedo", "auto-restart", \
    "--directory=.", "--pattern=*.py", "--recursive", "--", \
    "python3", "-Xfrozen_modules=off", "-m", "debugpy", "--listen", "0.0.0.0:5679", \
    "-m", "celery", "-A", "app", "worker", "-l", "INFO", "--uid=nobody", "--gid=nogroup"]
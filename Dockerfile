# syntax=docker/dockerfile:1

# ---- builder stage: resolve dependencies with uv, discarded afterwards ----
FROM python:3.12-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# flask and nanosip are pure Python, so this almost never needs a compiler.
# build-base/musl-dev are kept only as a safety net for architectures where
# a prebuilt wheel might be missing - either way, none of this reaches the
# final image.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    apk add --no-cache --virtual .build-deps build-base musl-dev \
    && uv sync --locked --no-install-project --no-dev \
    && apk del .build-deps

# ---- final stage: minimal runtime ----
FROM python:3.12-alpine

WORKDIR /app

RUN adduser -D -H ringer

COPY --from=builder --chown=ringer:ringer /app/.venv /app/.venv
COPY ring_phone.py .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER ringer
EXPOSE 5005

CMD ["python3", "ring_phone.py"]

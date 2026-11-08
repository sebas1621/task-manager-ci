# syntax=docker/dockerfile:1
# Build context is api/. Same exact pinned base for every stage (never `latest`).

# ---------------------------------------------------------------------------
# Stage 1: builder - installs runtime dependencies into an isolated venv.
# ---------------------------------------------------------------------------
FROM python:3.12.16-slim-trixie AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# The venv is the only artifact copied to the final image, so pip and any
# build leftovers never reach it.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements.txt first: this layer is rebuilt only when the
# dependencies change, not on every source edit (layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: runtime - minimal image with the venv and the application code.
# ---------------------------------------------------------------------------
FROM python:3.12.16-slim-trixie AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Unprivileged system user with a fixed UID/GID (predictable file ownership).
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Dependencies come from the builder; code is copied last (changes most often).
# Files stay owned by root: the app user can read them but not modify them.
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

USER app

EXPOSE 8000

# Migrations run at every container start (idempotent: no-op when up to date),
# then uvicorn replaces the shell via `exec` so it is PID 1 and receives
# SIGTERM from `docker stop`. `--factory` because app.main exposes create_app().
# DB settings come from environment variables.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000"]

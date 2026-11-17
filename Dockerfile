# One image for the whole app: API, frontend and OCR models.
# Runs as-is on a Hugging Face Docker Space (port 7860, user 1000) and with `docker compose up`.
FROM python:3.12-slim

# OpenCV (used by mokuro) needs these at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv

# Hugging Face Spaces run the container as uid 1000; the model caches live in its home.
RUN useradd --create-home --uid 1000 user
USER user
# Where compose mounts the library volume; created here so the volume belongs to `user`.
RUN mkdir -p /home/user/data
ENV HOME=/home/user \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH=/home/user/app/backend/.venv/bin:$PATH
WORKDIR /home/user/app/backend

# Dependencies first, so code changes don't reinstall them.
COPY --chown=user backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=user backend/app ./app
RUN python -m app.prefetch
COPY --chown=user frontend ../frontend

ENV ENV=prod \
    PORT=7860 \
    HF_HUB_OFFLINE=1
EXPOSE 7860
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

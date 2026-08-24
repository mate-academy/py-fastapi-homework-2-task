FROM python:3.10-slim

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV ALEMBIC_CONFIG=/usr/src/alembic/alembic.ini

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    postgresql-client \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binaries from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory for the application
WORKDIR /usr/src/app

# Copy dependency definition files
COPY ./pyproject.toml ./uv.lock* /usr/src/app/
COPY ./alembic.ini /usr/src/alembic/alembic.ini

# Install project dependencies into .venv (excluding dev group) using build cache
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy source code and scripts
COPY ./src /usr/src/app/src
COPY ./commands /commands

# Install the project itself and add the virtual environment to PATH
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/usr/src/app/.venv/bin:$PATH"

# Convert line endings to Unix style and set execution permissions
RUN dos2unix /commands/*.sh && chmod +x /commands/*.sh
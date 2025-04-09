# Stage 1: Build environment
FROM python:3.13 AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -LsSf https://github.com/astral-sh/uv/releases/download/0.6.12/uv-installer.sh | sh

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml /app/
RUN /root/.local/bin/uv sync

ARG GIT_COMMIT_HASH
RUN echo $GIT_COMMIT_HASH > /app/git_commit_hash.txt

# Stage 2: Production environment
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl libpq-dev libpango-1.0-0 libpangoft2-1.0-0 libmagic1 poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project files
COPY --from=builder /app/.venv/ /app/.venv/
COPY --from=builder /app/uv.lock /app/
COPY phasesix/ /app/
COPY entrypoints/ /app/
COPY --from=builder /app/git_commit_hash.txt /app/

# Expose port
EXPOSE 4343

# Run Django server
CMD ["/app/.venv/bin/hypercorn", "-w", "5", "-b", "0.0.0.0:4444", "phasesix.asgi:application"]


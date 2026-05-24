FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project

COPY src ./src
RUN uv sync --no-dev --frozen

RUN mkdir -p /app/data

ENV DATA_DIR=/app/data

CMD ["uv", "run", "python", "-m", "ticket_monitor.main"]

FROM python:3.12-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN uv sync --no-dev

RUN mkdir -p /app/data

ENV DATA_DIR=/app/data

CMD ["uv", "run", "python", "-m", "ticket_monitor.main"]

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY packages /app/packages
COPY skills /app/skills
COPY lessons /app/lessons
COPY workflows /app/workflows
COPY agents /app/agents
COPY tests /app/tests
COPY molt /app/molt
COPY apps /app/apps
COPY AGENTS.md /app/AGENTS.md
COPY Skills_Guide.md /app/Skills_Guide.md
COPY Skills_Guide.png /app/Skills_Guide.png

RUN pip install -e . \
    && useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

CMD ["./molt", "skill-builder", "--help"]

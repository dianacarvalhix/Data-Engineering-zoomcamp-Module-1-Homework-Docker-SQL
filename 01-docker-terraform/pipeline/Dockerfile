FROM python:3.12-slim

# Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

# Add virtual env to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock .python-version ./

# Install dependencies
RUN uv sync --locked

# Copy your code
COPY ingest_green.py .

# Run script
ENTRYPOINT ["python", "ingest_green.py"]
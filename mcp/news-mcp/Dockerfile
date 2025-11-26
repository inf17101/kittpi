FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS base
WORKDIR /app

# RUN apt-get update && apt-get install --no-install-recommends -y libspeexdsp-dev \
#         && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN uv venv \
    && echo "ENV PATH=/app/.venv/bin:$PATH" >> /uv_vars.sh \
    && uv sync

ENV PATH="/app/.venv/bin:$PATH"

FROM base AS prod
CMD ["python", "-u", "/app/news_mcp.py"]
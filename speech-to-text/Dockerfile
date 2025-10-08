FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS base
ARG VOSK_DEFAULT_MODEL="vosk-model-small-en-us-0.15.zip"
WORKDIR /app

# RUN apt-get update && apt-get install --no-install-recommends -y libspeexdsp-dev \
#         && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN uv venv \
    && echo "ENV PATH=/app/.venv/bin:$PATH" >> /uv_vars.sh \
    && uv sync

ENV PATH="/app/.venv/bin:$PATH"

FROM base AS prod
RUN mkdir -p /root/.cache/vosk \
    && curl -L https://alphacephei.com/vosk/models/${VOSK_DEFAULT_MODEL} -o /tmp/${VOSK_DEFAULT_MODEL} \
    && unzip -d /root/.cache/vosk /tmp/${VOSK_DEFAULT_MODEL}
CMD ["python", "-u", "/app/speech-to-text.py", "--model", "en-us", "--samplerate", "16000"]
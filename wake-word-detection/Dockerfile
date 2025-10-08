FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS base

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y libspeexdsp-dev \
        && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN mkdir /app/models && curl -L https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/hey_rhasspy_v0.1.onnx -o /app/models/hey_rhasspy_v0.1.onnx

RUN uv venv \
    && echo "ENV PATH=/app/.venv/bin:$PATH" >> /uv_vars.sh \
    && uv sync

ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p /app/.venv/lib/python3.11/site-packages/openwakeword/resources/models
RUN curl -L https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.onnx -o /app/.venv/lib/python3.11/site-packages/openwakeword/resources/models/melspectrogram.onnx
RUN curl -L https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.onnx -o /app/.venv/lib/python3.11/site-packages/openwakeword/resources/models/embedding_model.onnx
RUN curl -L https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/silero_vad.onnx -o /app/.venv/lib/python3.11/site-packages/openwakeword/resources/models/silero_vad.onnx

FROM base AS prod
CMD ["python", "-u", "/app/detect_wake_word_from_mqtt.py", "--model_path", "/app/models/hey_rhasspy_v0.1.onnx", "--inference_framework", "onnx"]
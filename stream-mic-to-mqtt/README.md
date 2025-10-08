# Stream mic to mqtt

The Python script records from the microphone in a stream and publishes the recorded chunks into an MQTT broker for further processing.

## Prerequisites

- [uv Python package manager](https://docs.astral.sh/uv/)

If not already running, start MQTT broker:

```shell
docker run --rm -it --net=host docker.io/eclipse-mosquitto:2
```

## Create virtualenv

```shell
uv venv --python 3.11.7
```

## Run

```shell
uv run stream_mic_to_mqtt.py
```
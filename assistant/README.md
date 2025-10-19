# Home Assistant

The home assistant uses the [OpenAI Agent SDK](https://openai.github.io/openai-agents-python/) with MCP tools.

## Prerequisites

- OPENAI_API_KEY

## Build

```shell
docker build -t home-assistant .
```

## Run

If not already running, start MQTT broker:

```shell
docker run --rm -it --net=host docker.io/eclipse-mosquitto:2
```

Start the home-assistant application:

```shell
docker run -it --rm --net=host -e OPENAI_API_KEY=sk-... home-assistant
```

Note: Provide the correct OpenAI API key as environment variable as run option.

If not already running, start the `stream_mic_to_mqtt` script like described in [../stream-mic-to-mqtt/README.md](../stream-mic-to-mqtt/README.md).
# Speech to text

The speecht-to-text application uses `vosk`. It contains small models in various languages (default: `vosk-model-small-en-us-0.15`) suitable for reliable speech-to-text on embeeded devices.

## Build

```shell
docker build -t speech-to-text .
```

## Run

If not already running, start MQTT broker:

```shell
docker run --rm -it --net=host docker.io/eclipse-mosquitto:2
```

Start the speech-to-text application:

```shell
docker run --rm --net=host speech-to-text
```

If not already running, start the `stream_mic_to_mqtt` script like described in [../stream-mic-to-mqtt/README.md](../stream-mic-to-mqtt/README.md).
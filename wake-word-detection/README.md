# Wake word detection

The wake word detection uses `openWakeWord` with the model to detect the wake words `Hey rhasspy`.

## Build

```shell
docker build -t wake-word-detection .
```

## Run

If not already running, start MQTT broker:

```shell
docker run --rm -it --net=host docker.io/eclipse-mosquitto:2
```

Start the wake word detection:

```shell
docker run -it --rm --net=host wake-word-detection
```

If not already running, start the `stream_mic_to_mqtt` script like described in [../stream-mic-to-mqtt/README.md](../stream-mic-to-mqtt/README.md).
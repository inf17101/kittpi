import pyaudio
import paho.mqtt.client as mqtt
import base64

# MQTT setup
# broker = "192.168.178.41"   # or your broker
broker = "localhost"   # or your broker
port = 1883
topic = "audio/stream"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(broker, port, 60)

# Audio setup
CHUNK = 1280        # Number of frames per buffer
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000        # Sample rate

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("🎙️ Streaming audio... Press Ctrl+C to stop.")

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        # Encode as base64 to avoid raw binary MQTT issues
        encoded = base64.b64encode(data).decode("utf-8")
        client.publish(topic, encoded)
except KeyboardInterrupt:
    print("\n🛑 Stopping stream...")

stream.stop_stream()
stream.close()
p.terminate()
client.disconnect()

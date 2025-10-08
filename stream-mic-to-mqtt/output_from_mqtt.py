import pyaudio
import paho.mqtt.client as mqtt
import base64

broker = "localhost"
port = 1883
topic = "audio/stream"

# Audio playback setup
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK)

def on_message(client, userdata, msg):
    decoded = base64.b64decode(msg.payload)
    stream.write(decoded)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(broker, port, 60)
client.subscribe(topic)

print("🎧 Listening to stream...")
client.loop_forever()
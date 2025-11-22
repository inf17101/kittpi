import numpy as np
import argparse
import paho.mqtt.client as mqtt
import paho.mqtt.publish as mqtt_publish
import base64
import json
from queue import Queue, Empty
import signal
from threading import Event, Thread

from vosk import Model, KaldiRecognizer

# Create a global event that can be used by other threads
stop_event = Event()
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def handle_stop_signals(signum, frame):
    print(f"Received stop signal, shutting down gracefully...")
    stop_event.set()
    client.disconnect()

# Register signal handlers
signal.signal(signal.SIGTERM, handle_stop_signals)
signal.signal(signal.SIGINT, handle_stop_signals)

parser = argparse.ArgumentParser()
parser.add_argument(
    "-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
parser.add_argument(
    "-r", "--samplerate", type=int, help="sampling rate")
args = parser.parse_args()
        
if args.model is None:
    model = Model(lang="en-us")
else:
    model = Model(lang=args.model)

broker = "localhost"
port = 1883
topic_wakeword = "wakeword/detected"
topic_audio = "audio/stream"
topic_instruction = "assistant/instruction"

rec = KaldiRecognizer(model, args.samplerate)
text_queue = Queue()
wakeword_event = Event()
SILENCE_TIME = 0.5

def on_message(client, userdata, msg):
    msg_topic = str(msg.topic)
    if msg_topic == topic_audio:
        if wakeword_event.is_set():
            decoded_chunk = base64.b64decode(msg.payload)
            # Get audio
            audio = bytes(decoded_chunk)
            if rec.AcceptWaveform(audio):
                full_result = json.loads(rec.Result())
                full_result = full_result.get("text", "")
                if full_result:
                    text_queue.put(full_result)
    elif msg_topic == topic_wakeword:
        if not wakeword_event.is_set():
            print("Wakeword was detected. Start speech-to-text.")
            wakeword_event.set()
    else:
        print(f"Ignoring message from unknown topic '{msg_topic}'.")

def forward_stt():
    text = ""
    while not stop_event.is_set():
        try:
            text_part = text_queue.get(timeout=SILENCE_TIME)
            text += text_part
        except Empty:
            if text:
                print(f"No text from stt since '{SILENCE_TIME}'. Forwarding input text: '{text}'")
                mqtt_publish.single(topic_instruction, text, hostname=broker, port=port)
                text = ""
                wakeword_event.clear()

client.on_message = on_message
client.connect(broker, port, 60)
client.subscribe(topic_wakeword)
client.subscribe(topic_audio)
forward_stt_thread = Thread(target=forward_stt, daemon=True, name="forward-stt-thread")
forward_stt_thread.start()
client.loop_forever()
forward_stt_thread.join()
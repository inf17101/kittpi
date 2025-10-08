import numpy as np
import argparse
import paho.mqtt.client as mqtt
import base64
import json

from vosk import Model, KaldiRecognizer

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
topic = "audio/stream"

rec = KaldiRecognizer(model, args.samplerate)

def on_message(client, userdata, msg):
    decoded_chunk = base64.b64decode(msg.payload)
    # Get audio
    # audio = np.frombuffer(decoded_chunk, dtype=np.int16)
    audio = bytes(decoded_chunk)
    if rec.AcceptWaveform(audio):
        full_result = json.loads(rec.Result())
        full_result = full_result["text"]
        if full_result:
            print(full_result)
    else:
        partial_part = json.loads(rec.PartialResult())
        partial_part = partial_part["partial"]
        if partial_part:
            print(partial_part)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(broker, port, 60)
client.subscribe(topic)
client.loop_forever()
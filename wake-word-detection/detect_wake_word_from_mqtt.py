# Copyright 2022 David Scripka. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Imports
import numpy as np
from openwakeword.model import Model
import argparse
import paho.mqtt.client as mqtt
import paho.mqtt.publish as mqtt_publish
import base64

# Parse input arguments
parser=argparse.ArgumentParser()
parser.add_argument(
    "--model_path",
    help="The path of a specific model to load",
    type=str,
    default="",
    required=False
)
parser.add_argument(
    "--inference_framework",
    help="The inference framework to use (either 'onnx' or 'tflite'",
    type=str,
    default='tflite',
    required=False
)

args=parser.parse_args()

# Load pre-trained openwakeword models
if args.model_path != "":
    wake_word_model = Model(wakeword_models=[args.model_path], inference_framework=args.inference_framework, enable_speex_noise_suppression=False, vad_threshold=0.5)
else:
    wake_word_model = Model(inference_framework=args.inference_framework, enable_speex_noise_suppression=False, vad_threshold=0.5)

n_models = len(wake_word_model.models.keys())

broker = "localhost"
port = 1883
topic_wakeword = "wakeword/detected"
topic_audio = "audio/stream"
SCORE_THRESHOLD = 0.5

def on_message(client, userdata, msg):
    decoded_chunk = base64.b64decode(msg.payload)
    # Get audio
    audio = np.frombuffer(decoded_chunk, dtype=np.int16)

    # Feed to openWakeWord model
    prediction = wake_word_model.predict(audio)

    for mdl in wake_word_model.prediction_buffer.keys():
        # Add scores in formatted table
        scores = list(wake_word_model.prediction_buffer[mdl])
        if scores[-1] > SCORE_THRESHOLD:
            print("Wake word detected!")
            mqtt_publish.single(topic_wakeword, True, hostname=broker, port=port)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(broker, port, 60)
client.subscribe(topic_audio)
client.loop_forever()


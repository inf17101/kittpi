import queue
import multiprocessing as mp
import sounddevice as sd
import numpy as np
from kokoro_onnx import Kokoro
from aiomqtt import Client
import asyncio
import time

broker = "localhost"
port = 1883
topic_reply = "assistant/reply"

# --------------------------------------------------------
AUDIO_RATE = 24000
CHUNK_MS = 400
AUDIO_CHUNK_SAMPLES = AUDIO_RATE * CHUNK_MS // 1000

WELCOME_MESSAGE = "Hello, I am your personal home assistant."


# --------------------------------------------------------
async def audio_playback_process(audio_queue: mp.Queue, stop_flag: mp.Event):
    sd.default.samplerate = AUDIO_RATE
    sd.default.channels = 1
    sd.default.dtype = "float32"

    stream = sd.OutputStream(blocksize=1024)
    stream.start()

    buffer = np.zeros(0, dtype=np.float32)

    while not stop_flag.is_set():
        try:
            (samples, sample_rate) = audio_queue.get(timeout=0.1)
            print("Got new audio for output.")
            if samples is not None:
                buffer = np.concatenate([buffer, samples])
        except queue.Empty:
            pass

        if len(buffer) >= AUDIO_CHUNK_SAMPLES:
            time.sleep(0.2)
            to_play = buffer[:AUDIO_CHUNK_SAMPLES]
            buffer = buffer[AUDIO_CHUNK_SAMPLES:]
            stream.write(to_play)
            
        if len(buffer) > 0:
            stream.write(buffer)
            buffer = np.zeros(0, dtype=np.float32)

    stream.stop()
    stream.close()

# --------------------------------------------------------
async def text_to_speech(audio_queue: mp.Queue):
    async with Client(broker, port=port) as client:
        kokoro = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
        samples, sample_rate = kokoro.create(WELCOME_MESSAGE,
                voice="af_heart",
                speed=1.0,
                lang="en-us",)
        audio_queue.put((samples, sample_rate))
        await client.subscribe(topic_reply)

        async for message in client.messages:
            assistant_reply = message.payload.decode()
            samples, sample_rate = kokoro.create(
                assistant_reply,
                voice="af_heart",
                speed=1.0,
                lang="en-us",
            )
            audio_queue.put((samples, sample_rate))


# --------------------------------------------------------
# PROCESS WRAPPER (sync)
# --------------------------------------------------------
def tts_process_main(audio_queue: mp.Queue):
    asyncio.run(text_to_speech(audio_queue))

def audio_playback_process_main(audio_queue: mp.Queue, stop_flag: mp.Event):
    asyncio.run(audio_playback_process(audio_queue, stop_flag))

# --------------------------------------------------------
if __name__ == "__main__":
    mp.set_start_method("spawn")

    audio_queue = mp.Queue(maxsize=10)
    stop_flag = mp.Event()

    tts_p = mp.Process(target=tts_process_main, args=(audio_queue,))
    audio_p = mp.Process(target=audio_playback_process_main,
                         args=(audio_queue, stop_flag))

    tts_p.start()
    audio_p.start()

    tts_p.join()
    stop_flag.set()
    audio_queue.put((None, None))
    audio_p.join()

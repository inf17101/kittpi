from aiomqtt import Client
import asyncio
import subprocess
import sys

broker = "localhost"
port = 1883
topic_reply = "assistant/reply"

async def text_to_speech():
    async with Client(broker, port=port) as client:
        await client.subscribe(topic_reply)
        print(f"Subscribed to mqtt topic '{topic_reply}' to wait for assistant replies.")

        async for message in client.messages:
            assistant_reply = message.payload.decode()
            print(f"Received assistant reply: '{assistant_reply}'")

            try:
                # Start Kokoro TTS process
                p = subprocess.Popen(
                    [sys.executable, "-m", "kokoro_tts", "-", "--stream", "--format", "wav"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE
                )

                # Send the text directly to kokoro_tts via stdin
                p.stdin.write(assistant_reply.encode())
                p.stdin.close()
                p.wait()

                # Optionally read or handle the audio output stream from stdout
                # (You could pipe this to a player or save to a file.)
                # output, _ = p.communicate()
                print(f"Text-to-speech process ended with exit code: {p.returncode}")

            except Exception as e:
                print(f"Error with text-to-speech: {e}")

asyncio.run(text_to_speech())

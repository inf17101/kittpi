from openai.types.shared import Reasoning
from agents import Runner, Agent, ModelSettings, SQLiteSession
from agents.mcp import MCPServerStreamableHttp
from agents.extensions.memory import EncryptedSession
from openai.types.responses import ResponseTextDeltaEvent
from aiomqtt import Client
import asyncio
from nltk.tokenize import sent_tokenize

broker = "localhost"
port = 1883
topic_instruction = "assistant/instruction"
topic_reply = "assistant/reply"

class SentenceStreamer:
    def __init__(self):
        self.buffer = ""  # Holds text not yet emitted

    def feed(self, chunk):
        """
        Feed a new chunk of text from the LLM stream.
        Returns a list of complete sentences ready to forward.
        """
        self.buffer += chunk
        sentences = sent_tokenize(self.buffer)

        # Emit all complete sentences except the last one (may be incomplete)
        if len(sentences) == 0:
            return []

        # Keep the last sentence in buffer for next chunk
        self.buffer = sentences[-1]

        # Return all sentences except the last (still in buffer)
        return sentences[:-1]

    def flush(self):
        """
        Call at the end to emit any leftover text as a sentence.
        """
        leftover = self.buffer.strip()
        self.buffer = ""
        return [leftover] if leftover else []

async def run_agent_on_incoming_instructions():

    # Create encrypted SQLite session
    underlying = SQLiteSession("user-1")

    session = EncryptedSession(
        session_id="user-1",
        underlying_session=underlying,
        encryption_key="secret-key",
        ttl=120,
    )

    async with MCPServerStreamableHttp(
        name="tagesschau_news",
        params={
            "url": "http://127.0.0.1:8001/mcp",
            # "headers": {"Authorization": f"Bearer {token}"},
            "timeout": 10,
        },
        cache_tools_list=True,
        max_retry_attempts=10,
    ) as server:
        assistant = Agent(
            name="Home Assistant",
            instructions="You are a helpful home assistant. Speak in friendly, natural sentences optimized for text to speech, without titles, lists, special characters, or formatting. Responses should not be too short. If tool output is not in English, translate and reply fully in English. Do not lie. If you do not know, say so. Only output normal sentences ending with periods.",
            model_settings=ModelSettings(max_tokens=200, tool_choice="required"),
            model="gpt-4o-mini",
            mcp_servers=[server],
        )

        async with Client(broker, port=port) as client:
            await client.subscribe(topic_instruction)
            print(f"Subscribed to mqtt topic '{topic_instruction}' to wait for incoming instructions.")

            async for message in client.messages:
                user_instruction = message.payload.decode()
                print(f"Received user instruction: '{user_instruction}'")

                try:
                    result = Runner.run_streamed(assistant, input=f"{user_instruction}", session=session)
                    streamer = SentenceStreamer()
                    async for event in result.stream_events():
                        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                            chunk = event.data.delta
                            for sentence in streamer.feed(chunk):
                                print(f"Forwarding assistant reply to mqtt topic '{topic_reply}'.")
                                print(f"Sentence: {sentence}")
                                await client.publish(topic_reply, sentence)
                    # Flush leftover
                    for sentence in streamer.flush():
                        print(f"Forwarding assistant reply to mqtt topic '{topic_reply}'.")
                        print(f"Sentence: {sentence}")
                        await client.publish(topic_reply, sentence)
                except Exception as e:
                    error_reply = f"Error processing request."
                    print(e)
                    print(f"Forwarding assistant error to mqtt topic '{topic_reply}'.")
                    await client.publish(topic_reply, error_reply)

asyncio.run(run_agent_on_incoming_instructions())
from openai.types.shared import Reasoning
from agents import Runner, Agent, ModelSettings
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
    assistant = Agent(
        name="Home Assistant",
        instructions="You are a helpful home assistant. Respond concise and friendly. No preamble or postamble. Do not lie. If you do not know, say it to the user.",
        model_settings=ModelSettings(reasoning=Reasoning(effort="minimal"), verbosity="low", max_tokens=500,),
        model="gpt-5-nano",
    )

    async with Client(broker, port=port) as client:
        await client.subscribe(topic_instruction)
        print(f"Subscribed to mqtt topic '{topic_instruction}' to wait for incoming instructions.")

        async for message in client.messages:
            user_instruction = message.payload.decode()
            print(f"Received user instruction: '{user_instruction}'")

            try:
                result = Runner.run_streamed(assistant, input=f"{user_instruction}")
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
                error_reply = f"Error processing request: {e}"
                print(f"Forwarding assistant error to mqtt topic '{topic_reply}'.")
                await client.publish(topic_reply, error_reply)

asyncio.run(run_agent_on_incoming_instructions())
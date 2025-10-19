from openai.types.shared import Reasoning
from agents import Runner, Agent, ModelSettings
from aiomqtt import Client
import asyncio

broker = "localhost"
port = 1883
topic_instruction = "assistant/instruction"
topic_reply = "assistant/reply"

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
                result = await Runner.run(assistant, f"{user_instruction}")
                assistant_reply = result.final_output
                print("Assistant's reply:", assistant_reply)
            except Exception as e:
                assistant_reply = f"Error processing request: {e}"

            # Publish reply
            print(f"Forwarding assistant reply to mqtt topic '{topic_reply}'.")
            await client.publish(topic_reply, assistant_reply)

asyncio.run(run_agent_on_incoming_instructions())
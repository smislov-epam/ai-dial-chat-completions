import asyncio
from dotenv import load_dotenv

# Load environment variables before importing modules that read env values.
load_dotenv(override=True)

from task.clients.client import DialClient
from task.clients.custom_client import CustomDialClient
from task.constants import DEFAULT_SYSTEM_PROMPT, API_KEY
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


async def start(stream: bool) -> None:
    if not API_KEY:
        raise RuntimeError("DIAL_API_KEY is missing. Set it in your environment or a .env file.")
 
    deployment_name = "gpt-4o"
    use_custom = input("Use CustomDialClient? (y/N): ").strip().lower() == "y"
    client = CustomDialClient(deployment_name) if use_custom else DialClient()

    # Create conversation and seed with system prompt.
    conversation = Conversation(messages=[])
    system_prompt = input("Enter system prompt (leave empty for default): ").strip() or DEFAULT_SYSTEM_PROMPT
    conversation.messages.append(Message(role=Role.SYSTEM, content=system_prompt))

    while True:
        user_message = input("You: ").strip()
        if user_message.lower() == "exit":
            break

        conversation.messages.append(Message(role=Role.USER, content=user_message))

        if stream:
            # Stream tokens from the API and collect the final content.
            assistant_msg = await client.stream_completion(conversation.messages)
        else:
            # Run blocking completion call in a thread to avoid blocking the event loop.
            assistant_msg = await asyncio.to_thread(client.get_completion, conversation.messages)

        conversation.messages.append(assistant_msg)
        print(f"\nAssistant: {assistant_msg.content}\n")

asyncio.run(
    start(True)
)

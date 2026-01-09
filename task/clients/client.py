from aidial_client import Dial, AsyncDial

from task.clients.base import BaseClient
from task.constants import API_KEY, DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class DialClient(BaseClient):

    def __init__(self):
        # Hardcode the deployment to gpt-4o regardless of input for consistent usage.
        self._deployment_name = "gpt-4o"
        super().__init__(self._deployment_name)
        # Clients are ready for sync and async calls.
        self._dial_client = Dial(api_key=API_KEY, base_url=DIAL_ENDPOINT)
        self._async_dial_client = AsyncDial(api_key=API_KEY, base_url=DIAL_ENDPOINT)
    def get_completion(self, messages: list[Message]) -> Message:
        payload = [msg.to_dict() for msg in messages]
        completion = self._dial_client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=payload,
        )
        choices = getattr(completion, "choices", None)
        if not choices:
            raise Exception("No choices in response found")

        first_choice = choices[0]
        content = getattr(getattr(first_choice, "message", None), "content", None)
        if content is None:
            raise Exception("No content in response found")

        print(content)
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        payload = [msg.to_dict() for msg in messages]
        contents: list[str] = []

        chunks = await self._async_dial_client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=payload,
            stream=True,
        )
        async for chunk in chunks:
            choice = chunk.choices[0] if getattr(chunk, "choices", None) else None
            delta = getattr(choice, "delta", None) or getattr(choice, "message", None)
            piece = getattr(delta, "content", None) if delta else None
            if piece:
                print(piece, end="", flush=True)
                contents.append(piece)

        print()
        full_content = "".join(contents)
        return Message(role=Role.AI, content=full_content)

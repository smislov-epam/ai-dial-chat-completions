import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import API_KEY, DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class CustomDialClient(BaseClient):
    _endpoint: str
    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"

    def get_completion(self, messages: list[Message]) -> Message:
        headers = {
            "api-key": API_KEY,
            "Content-Type": "application/json",
        }
        request_data = {
            "messages": [msg.to_dict() for msg in messages],
        }

        response = requests.post(self._endpoint, headers=headers, json=request_data)
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        payload = response.json()
        choices = payload.get("choices", [])
        if not choices:
            raise Exception("No choices in response found")

        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise Exception("No content in response found")

        print(content)
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        headers = {
            "api-key": API_KEY,
            "Content-Type": "application/json",
        }
        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages],
        }

        contents: list[str] = []

        async with aiohttp.ClientSession() as session:
            async with session.post(self._endpoint, headers=headers, json=request_data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {text}")

                async for raw_chunk in resp.content:
                    chunk = raw_chunk.decode().strip()
                    if not chunk:
                        continue
                    if not chunk.startswith("data: "):
                        continue
                    data_part = chunk[6:]
                    if data_part == "[DONE]":
                        break

                    data_json = json.loads(data_part)
                    piece = self._get_content_snippet(data_json)
                    if piece:
                        print(piece, end="", flush=True)
                        contents.append(piece)

        print()
        full_content = "".join(contents)
        return Message(role=Role.AI, content=full_content)

    @staticmethod
    def _get_content_snippet(data: dict) -> str | None:
        try:
            choice = data.get("choices", [{}])[0]
            delta = choice.get("delta") or choice.get("message") or {}
            return delta.get("content")
        except Exception:
            return None


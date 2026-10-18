"""Explicit deterministic test/demo model. Never selected by the real factory."""
import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field


class FixtureChatModel(BaseChatModel):
    responses: list[Any] = Field(default_factory=list)
    calls: list[Any] = Field(default_factory=list, exclude=True)

    @property
    def _llm_type(self):
        return "explicit-intelligence-fixture"

    def _generate(self, *args, **kwargs):
        raise RuntimeError("Fixture requires async invocation")

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls.append(messages)
        if not self.responses:
            raise RuntimeError("Explicit fixture responses exhausted")
        value = self.responses.pop(0)
        if isinstance(value, BaseException):
            raise value
        message = value if isinstance(value, AIMessage) else AIMessage(
            content=value if isinstance(value, str) else json.dumps(value, default=str))
        return ChatResult(generations=[ChatGeneration(message=message)])

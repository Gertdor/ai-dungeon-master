"""LLM client for interacting with OpenRouter API."""

import json
from typing import Any, Iterator, Optional

from openai import OpenAI

from ..config import Config, get_config
from .types import (
    ChatMessage,
    ChatRole,
    FunctionCall,
    LLMResponse,
    StreamChunk,
    Tool,
    ToolCall,
)


class LLMClient:
    """Client for making LLM calls via OpenRouter."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the LLM client.

        Args:
            config: Configuration object. If None, uses global config.
        """
        self.config = config or get_config()

        # OpenRouter uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=self.config.openrouter_api_key,
            base_url=self.config.openrouter_base_url,
        )

    @staticmethod
    def _serialize_tool_calls(tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Serialize tool calls for the API, ensuring arguments is a JSON string."""
        return [
            {
                **tc,
                "function": {
                    **tc["function"],
                    "arguments": json.dumps(tc["function"]["arguments"])
                    if isinstance(tc["function"]["arguments"], dict)
                    else tc["function"]["arguments"],
                },
            }
            for tc in tool_calls
        ]

    def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[list[Tool]] = None,
    ) -> LLMResponse:
        """Make a chat completion request.

        Args:
            messages: List of chat messages
            model: Model to use (defaults to dm_model from config)
            temperature: Sampling temperature (defaults to config)
            max_tokens: Maximum tokens to generate (defaults to config)
            tools: Optional list of tools the model can call

        Returns:
            LLMResponse with content and/or tool calls
        """
        # Use defaults from config if not specified
        model = model or self.config.dm_model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # Convert messages to dict format
        messages_dict = [
            {
                "role": msg.role.value,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {}),
                **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {}),
                **({"tool_calls": self._serialize_tool_calls(msg.tool_calls)} if msg.tool_calls else {}),
            }
            for msg in messages
        ]

        # Prepare request parameters
        request_params: dict[str, Any] = {
            "model": model,
            "messages": messages_dict,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add tools if provided
        if tools:
            request_params["tools"] = [tool.model_dump() for tool in tools]

        # Make API call
        response = self.client.chat.completions.create(**request_params)

        # Parse response
        choice = response.choices[0]
        message = choice.message

        # Extract tool calls if present
        tool_calls = None
        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    type=tc.type,
                    function=FunctionCall(
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments)
                        if isinstance(tc.function.arguments, str)
                        else tc.function.arguments,
                    ),
                )
                for tc in message.tool_calls
            ]

        # Extract usage information
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage=usage,
        )

    def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[list[Tool]] = None,
    ) -> Iterator[StreamChunk]:
        """Make a streaming chat completion request.

        Args:
            messages: List of chat messages
            model: Model to use (defaults to dm_model from config)
            temperature: Sampling temperature (defaults to config)
            max_tokens: Maximum tokens to generate (defaults to config)
            tools: Optional list of tools the model can call

        Yields:
            StreamChunk objects with content deltas
        """
        # Use defaults from config if not specified
        model = model or self.config.dm_model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # Convert messages to dict format
        messages_dict = [
            {
                "role": msg.role.value,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {}),
                **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {}),
                **({"tool_calls": self._serialize_tool_calls(msg.tool_calls)} if msg.tool_calls else {}),
            }
            for msg in messages
        ]

        # Prepare request parameters
        request_params: dict[str, Any] = {
            "model": model,
            "messages": messages_dict,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        # Add tools if provided
        if tools:
            request_params["tools"] = [tool.model_dump() for tool in tools]

        # Make streaming API call
        stream = self.client.chat.completions.create(**request_params)

        # Accumulate tool call information
        tool_call_accumulator: dict[int, dict[str, Any]] = {}

        for chunk in stream:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            # Handle content delta
            if delta.content:
                yield StreamChunk(
                    content=delta.content,
                    finish_reason=choice.finish_reason,
                )

            # Handle tool call deltas
            if hasattr(delta, "tool_calls") and delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_call_accumulator:
                        tool_call_accumulator[idx] = {
                            "id": tc_delta.id or "",
                            "type": tc_delta.type or "function",
                            "function": {"name": "", "arguments": ""},
                        }

                    if tc_delta.id:
                        tool_call_accumulator[idx]["id"] = tc_delta.id
                    if tc_delta.type:
                        tool_call_accumulator[idx]["type"] = tc_delta.type
                    if hasattr(tc_delta, "function") and tc_delta.function:
                        if tc_delta.function.name:
                            tool_call_accumulator[idx]["function"]["name"] = (
                                tc_delta.function.name
                            )
                        if tc_delta.function.arguments:
                            tool_call_accumulator[idx]["function"]["arguments"] += (
                                tc_delta.function.arguments
                            )

            # Yield finish event with accumulated tool calls
            if choice.finish_reason:
                tool_calls = None
                if tool_call_accumulator:
                    tool_calls = [
                        ToolCall(
                            id=tc["id"],
                            type=tc["type"],
                            function=FunctionCall(
                                name=tc["function"]["name"],
                                arguments=json.loads(tc["function"]["arguments"])
                                if tc["function"]["arguments"]
                                else {},
                            ),
                        )
                        for tc in tool_call_accumulator.values()
                    ]

                yield StreamChunk(
                    content=None,
                    finish_reason=choice.finish_reason,
                    tool_calls=tool_calls,
                )

    def create_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
    ) -> Tool:
        """Create a tool definition.

        Args:
            name: Function name
            description: Function description
            parameters: JSON schema for function parameters

        Returns:
            Tool object
        """
        return Tool(
            type="function",
            function={
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        )

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


RouteType = Literal[
    "command_exec",
    "file_read",
    "docker_inspect",
    "chat_fallback",
    "blocked",
    "invalid",
]


class RouteRequest(BaseModel):
    channel: str
    chat_id: str
    message_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("channel", "chat_id", mode="before")
    @classmethod
    def validate_non_empty_string(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("must be a string")
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("message_text", mode="before")
    @classmethod
    def validate_message_text(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("must be a string")
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class RouteResponse(BaseModel):
    ok: bool
    route: RouteType
    executed: bool
    fallback_used: bool
    reply_text: str
    details: dict[str, Any] = Field(default_factory=dict)

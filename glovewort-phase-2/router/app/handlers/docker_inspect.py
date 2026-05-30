from __future__ import annotations

from ..formatters import format_exec_reply
from ..logging_utils import log_event
from ..models import RouteRequest, RouteResponse
from ..safety import docker_inspect_allowed
from .local_exec import _run_command


def handle_docker_inspect(request: RouteRequest) -> RouteResponse:
    raw = request.message_text.strip()
    lowered = raw.lower()

    if lowered.startswith("docker compose ps"):
        command = "docker-compose ps"
        requested_command = raw
    elif lowered.startswith("docker ps"):
        command = "docker-compose ps"
        requested_command = raw
    elif lowered.startswith("cek container"):
        command = "docker-compose ps"
        requested_command = raw
    else:
        command = raw
        requested_command = raw

    allowed, reason = docker_inspect_allowed(command)
    if not allowed:
        log_event("docker_blocked", command=command, requested_command=requested_command, reason=reason, policy="phase2A-docker-readonly")
        return RouteResponse(
            ok=False,
            route="blocked",
            executed=False,
            fallback_used=False,
            reply_text="Perintah Docker ditolak oleh kebijakan phase-2.",
            details={"reason": reason, "policy": "phase2A-docker-readonly", "matched_command": command, "requested_command": requested_command},
        )

    result = _run_command(command)
    result["requested_command"] = requested_command
    result["executed_command"] = command
    return RouteResponse(
        ok=True,
        route="docker_inspect",
        executed=True,
        fallback_used=False,
        reply_text=format_exec_reply(result),
        details=result,
    )

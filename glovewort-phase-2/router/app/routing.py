from __future__ import annotations

from .handlers.docker_inspect import handle_docker_inspect
from .handlers.file_read import handle_file_read
from .handlers.local_exec import handle_command_exec
from .handlers.phase1_fallback import handle_phase1_fallback
from .models import RouteRequest, RouteResponse


def classify_request(request: RouteRequest) -> RouteResponse:
    text = request.message_text.strip()
    lowered = text.lower()

    if lowered.startswith("jalankan ") or lowered.startswith("run "):
        return handle_command_exec(request)

    if lowered.startswith("baca ") or lowered.startswith("read "):
        return handle_file_read(request)

    if lowered.startswith("docker ps") or lowered.startswith("docker compose ps") or lowered.startswith("cek container"):
        return handle_docker_inspect(request)

    return handle_phase1_fallback(request)

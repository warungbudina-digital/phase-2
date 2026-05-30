from __future__ import annotations

import re

from .handlers.docker_inspect import handle_docker_inspect
from .handlers.file_read import handle_file_read
from .handlers.local_exec import handle_command_exec
from .handlers.phase1_fallback import handle_phase1_fallback
from .models import RouteRequest, RouteResponse

_SAFE_COMMAND_PATTERNS = [
    r"docker\s+compose\s+ps",
    r"docker\s+ps",
    r"docker-compose\s+ps",
    r"docker\s+images",
    r"ls\s+-la",
    r"df\s+-h",
    r"whoami",
    r"pwd",
    r"ls",
]

_FILE_PATTERNS = [
    r"(?:baca|read)\s+([^\n]+?)(?:\s+lalu\s+ringkas)?(?:[!?]|$)",
]

_SUMMARY_HINT = re.compile(r"\b(lalu\s+ringkas|ringkas|summarize|summary)\b", re.IGNORECASE)


def _with_message(request: RouteRequest, message_text: str) -> RouteRequest:
    return request.model_copy(update={"message_text": message_text})


def _extract_safe_command(text: str) -> str | None:
    lowered = text.lower()
    for pattern in _SAFE_COMMAND_PATTERNS:
        match = re.search(rf"\b({pattern})\b", lowered)
        if match:
            return match.group(1)
    return None


def _extract_file_request(text: str) -> tuple[str, bool] | None:
    for pattern in _FILE_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        path_part = match.group(1).strip().rstrip("?!,")
        summarize = bool(_SUMMARY_HINT.search(text))
        return path_part, summarize
    return None


def classify_request(request: RouteRequest) -> RouteResponse:
    text = request.message_text.strip()
    lowered = text.lower()

    if lowered.startswith("jalankan ") or lowered.startswith("run "):
        return handle_command_exec(request)

    if lowered.startswith("baca ") or lowered.startswith("read "):
        return handle_file_read(request)

    if lowered.startswith("docker ps") or lowered.startswith("docker compose ps") or lowered.startswith("cek container"):
        return handle_docker_inspect(request)

    extracted_command = _extract_safe_command(text)
    if extracted_command is not None:
        if extracted_command in {"docker ps", "docker compose ps", "docker-compose ps", "docker images"}:
            return handle_docker_inspect(_with_message(request, extracted_command))
        return handle_command_exec(_with_message(request, f"jalankan {extracted_command}"))

    extracted_file = _extract_file_request(text)
    if extracted_file is not None:
        path_part, summarize = extracted_file
        normalized = f"baca {path_part}"
        if summarize:
            normalized += " lalu ringkas"
        return handle_file_read(_with_message(request, normalized))

    if "cek container" in lowered:
        return handle_docker_inspect(_with_message(request, "cek container"))

    return handle_phase1_fallback(request)

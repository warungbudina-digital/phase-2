from __future__ import annotations

import os
from pathlib import Path

SAFE_EXACT_COMMANDS = {
    "pwd",
    "ls",
    "ls -la",
    "whoami",
    "docker ps",
    "docker compose ps",
    "docker-compose ps",
    "docker images",
    "df -h",
}

BLOCKED_SUBSTRINGS = {
    " rm ",
    "rm -",
    "shutdown",
    "reboot",
    "poweroff",
    "mkfs",
    " dd ",
    "docker rm",
    "docker stop",
    "docker kill",
    "docker system prune",
    "apt ",
    "apt-get",
    "pip install",
    "curl http",
    "wget http",
}


def normalize_command(command: str) -> str:
    return " ".join(command.strip().split())


def is_command_allowed(command: str) -> tuple[bool, str]:
    normalized = normalize_command(command)
    lowered = f" {normalized.lower()} "

    for blocked in BLOCKED_SUBSTRINGS:
        if blocked in lowered:
            return False, f"blocked by rule: {blocked.strip()}"

    if normalized in SAFE_EXACT_COMMANDS:
        return True, "allowed exact command"

    if normalized.startswith("cat "):
        return True, "allowed cat command subject to path validation"

    return False, "command not in allowlist"


def resolve_allowed_path(raw_path: str, workspace_root: str) -> tuple[bool, str, str]:
    if not raw_path.strip():
        return False, "", "empty path"

    root = Path(workspace_root).resolve()
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = root / candidate

    try:
        resolved = candidate.resolve()
    except Exception as exc:
        return False, "", f"resolve failed: {exc}"

    try:
        resolved.relative_to(root)
    except ValueError:
        return False, str(resolved), "path outside allowed root"

    return True, str(resolved), "allowed"


def ensure_text_file(path: str) -> tuple[bool, str]:
    try:
        with open(path, "rb") as fh:
            sample = fh.read(2048)
    except Exception as exc:
        return False, f"read failed: {exc}"

    if b"\x00" in sample:
        return False, "binary file not allowed in phase-2A"

    return True, "text-like file"


def docker_inspect_allowed(command: str) -> tuple[bool, str]:
    normalized = normalize_command(command)
    if normalized in {"docker ps", "docker compose ps", "docker-compose ps", "docker images"}:
        return True, "allowed docker inspect command"
    return False, "docker command not allowed in phase-2A"


def get_exec_timeout(default: int = 20) -> int:
    try:
        return int(os.getenv("ROUTER_EXEC_TIMEOUT", str(default)))
    except Exception:
        return default


def get_max_output_chars(default: int = 4000) -> int:
    try:
        return int(os.getenv("ROUTER_MAX_OUTPUT_CHARS", str(default)))
    except Exception:
        return default


def get_workspace_root() -> str:
    return os.getenv("ROUTER_WORKSPACE_ROOT", "/workspace")

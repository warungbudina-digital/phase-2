from __future__ import annotations

import subprocess
import time
from typing import Any

from ..formatters import format_exec_reply, truncate_output
from ..logging_utils import log_event
from ..models import RouteRequest, RouteResponse
from ..safety import (
    ensure_text_file,
    get_exec_timeout,
    get_workspace_root,
    is_command_allowed,
    normalize_command,
    resolve_allowed_path,
)


def _run_command(command: str) -> dict[str, Any]:
    start = time.monotonic()
    proc = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=get_exec_timeout(),
        cwd=get_workspace_root(),
    )
    duration_ms = int((time.monotonic() - start) * 1000)
    stdout, stdout_truncated = truncate_output(proc.stdout)
    stderr, stderr_truncated = truncate_output(proc.stderr)
    result = {
        "command": command,
        "exit_code": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": duration_ms,
        "truncated": stdout_truncated or stderr_truncated,
    }
    log_event(
        "command_executed",
        command=command,
        exit_code=proc.returncode,
        duration_ms=duration_ms,
        truncated=result["truncated"],
    )
    return result


def handle_command_exec(request: RouteRequest) -> RouteResponse:
    raw = request.message_text.strip()
    command = raw.split(" ", 1)[1].strip() if " " in raw else ""
    if not command:
        log_event("command_invalid", raw_text=raw, reason="missing_command_after_prefix")
        return RouteResponse(
            ok=False,
            route="invalid",
            executed=False,
            fallback_used=False,
            reply_text="Perintah router tidak valid.",
            details={"reason": "missing_command_after_prefix"},
        )

    allowed, reason = is_command_allowed(command)
    if not allowed:
        log_event("command_blocked", command=command, reason=reason, policy="phase2A-safe-allowlist")
        return RouteResponse(
            ok=False,
            route="blocked",
            executed=False,
            fallback_used=False,
            reply_text="Perintah ditolak oleh kebijakan keamanan phase-2.",
            details={"reason": reason, "policy": "phase2A-safe-allowlist", "matched_command": command},
        )

    if normalize_command(command).startswith("cat "):
        path_part = command[4:].strip()
        ok, resolved, why = resolve_allowed_path(path_part, get_workspace_root())
        if not ok:
            log_event("path_blocked", matched_path=path_part, reason=why, policy="phase2A-path-root")
            return RouteResponse(
                ok=False,
                route="blocked",
                executed=False,
                fallback_used=False,
                reply_text="Path ditolak oleh kebijakan keamanan phase-2.",
                details={"reason": why, "policy": "phase2A-path-root", "matched_path": path_part},
            )
        text_ok, text_reason = ensure_text_file(resolved)
        if not text_ok:
            log_event("file_blocked", matched_path=resolved, reason=text_reason, policy="phase2A-text-file-only")
            return RouteResponse(
                ok=False,
                route="blocked",
                executed=False,
                fallback_used=False,
                reply_text="File ditolak oleh kebijakan phase-2.",
                details={"reason": text_reason, "policy": "phase2A-text-file-only", "matched_path": resolved},
            )
        command = f"cat {resolved}"

    result = _run_command(command)
    return RouteResponse(
        ok=True,
        route="command_exec",
        executed=True,
        fallback_used=False,
        reply_text=format_exec_reply(result),
        details=result,
    )

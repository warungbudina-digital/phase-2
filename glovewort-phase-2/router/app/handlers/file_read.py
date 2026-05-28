from __future__ import annotations

from pathlib import Path

from ..formatters import format_file_read_reply, truncate_output
from ..logging_utils import log_event
from ..models import RouteRequest, RouteResponse
from ..safety import ensure_text_file, get_workspace_root, resolve_allowed_path


def handle_file_read(request: RouteRequest) -> RouteResponse:
    raw = request.message_text.strip()
    lowered = raw.lower()

    prefix = "baca " if lowered.startswith("baca ") else "read "
    rest = raw[len(prefix):].strip()
    summarize = False

    if " lalu ringkas" in rest.lower():
        summarize = True
        idx = rest.lower().rfind(" lalu ringkas")
        path_part = rest[:idx].strip()
    else:
        path_part = rest.strip()

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

    data = Path(resolved).read_text(encoding="utf-8", errors="replace")
    excerpt, truncated = truncate_output(data)
    reply, mode = format_file_read_reply(path_part, excerpt, summarize)

    log_event(
        "file_read",
        path=path_part,
        resolved_path=resolved,
        bytes_read=len(data.encode("utf-8", errors="ignore")),
        truncated=truncated,
        summary_used=summarize,
    )

    return RouteResponse(
        ok=True,
        route="file_read",
        executed=True,
        fallback_used=False,
        reply_text=reply,
        details={
            "path": path_part,
            "resolved_path": resolved,
            "mode": mode,
            "bytes_read": len(data.encode("utf-8", errors="ignore")),
            "truncated": truncated,
            "summary_used": summarize,
            "raw_excerpt": excerpt,
        },
    )

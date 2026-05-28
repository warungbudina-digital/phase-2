from __future__ import annotations

from typing import Any

from .safety import get_max_output_chars


def truncate_output(text: str) -> tuple[str, bool]:
    limit = get_max_output_chars()
    if len(text) <= limit:
        return text, False
    return text[:limit] + "\n...[truncated]", True


def format_exec_reply(result: dict[str, Any]) -> str:
    parts = [
        f"Perintah: {result['command']}",
        f"Exit code: {result['exit_code']}",
    ]
    if result.get("stdout"):
        parts.append(f"Hasil:\n{result['stdout'].rstrip()}")
    if result.get("stderr"):
        parts.append(f"Error:\n{result['stderr'].rstrip()}")
    return "\n".join(parts)


def format_file_read_reply(path_part: str, excerpt: str, summarize: bool) -> tuple[str, str]:
    if summarize:
        return (
            f"{path_part} berhasil dibaca. Ringkasan belum diimplementasikan di phase-2A; cuplikan aktual:\n{excerpt}",
            "read_and_summarize_stub",
        )
    return (f"Isi {path_part}:\n{excerpt}", "read_only")

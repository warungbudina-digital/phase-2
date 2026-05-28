from __future__ import annotations

"""Compatibility shim during handler-family migration.

New code should import from `app.handlers.<family>` directly.
"""

from .handlers.docker_inspect import handle_docker_inspect
from .handlers.file_read import handle_file_read
from .handlers.local_exec import handle_command_exec
from .handlers.phase1_fallback import handle_phase1_fallback

__all__ = [
    "handle_command_exec",
    "handle_file_read",
    "handle_docker_inspect",
    "handle_phase1_fallback",
]

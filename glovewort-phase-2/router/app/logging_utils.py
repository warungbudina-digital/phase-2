from __future__ import annotations

import json
import logging
import os
from typing import Any

_LOG_LEVEL = os.getenv("ROUTER_LOG_LEVEL", "info").upper()

logger = logging.getLogger("glovewort_phase2_router")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(getattr(logging, _LOG_LEVEL, logging.INFO))
logger.propagate = False


def _compact(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _compact(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_compact(v) for v in data]
    if isinstance(data, str):
        return data if len(data) <= 300 else data[:300] + "...[truncated]"
    return data


def log_event(event: str, **fields: Any) -> None:
    payload = {"event": event, **_compact(fields)}
    logger.info(json.dumps(payload, ensure_ascii=False))

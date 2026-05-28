from __future__ import annotations

from ..fallback import delegate_chat_fallback
from ..models import RouteRequest, RouteResponse


def handle_phase1_fallback(request: RouteRequest) -> RouteResponse:
    return delegate_chat_fallback(request)

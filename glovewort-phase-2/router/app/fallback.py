from __future__ import annotations

import os
from typing import Any

import httpx

from .logging_utils import log_event
from .models import RouteRequest, RouteResponse


def _phase1_bridge_base() -> str:
    return os.getenv("PHASE1_BRIDGE_BASE_URL", "").rstrip("/")


def phase1_chat_completions_url() -> str:
    base = _phase1_bridge_base()
    if not base:
        return ""
    return f"{base}/chat/completions"


def _phase1_bridge_api_key() -> str:
    return os.getenv("PHASE1_BRIDGE_API_KEY", "")


def _phase1_model() -> str:
    return os.getenv("PHASE1_FALLBACK_MODEL", "qwen2.5-coder:3b-instruct")


def router_bridge_api_key() -> str:
    return os.getenv("ROUTER_BRIDGE_API_KEY", os.getenv("PHASE1_BRIDGE_API_KEY", ""))


def build_phase1_headers(incoming_authorization: str | None = None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = _phase1_bridge_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif incoming_authorization:
        headers["Authorization"] = incoming_authorization
    return headers


def check_router_auth(authorization: str | None) -> str | None:
    expected_key = router_bridge_api_key()
    if not expected_key:
        return None
    expected = f"Bearer {expected_key}"
    if authorization != expected:
        return "Unauthorized"
    return None


def delegate_chat_fallback(request: RouteRequest) -> RouteResponse:
    url = phase1_chat_completions_url()
    if not url:
        log_event("chat_fallback_failed", reason="missing_phase1_bridge_base_url")
        return RouteResponse(
            ok=False,
            route="chat_fallback",
            executed=False,
            fallback_used=True,
            reply_text="Chat fallback gagal: PHASE1_BRIDGE_BASE_URL belum diatur.",
            details={"reason": "missing_phase1_bridge_base_url", "delegated": False},
        )

    payload: dict[str, Any] = {
        "model": _phase1_model(),
        "messages": [{"role": "user", "content": request.message_text}],
        "stream": False,
    }

    headers = build_phase1_headers()

    log_event("chat_fallback_started", upstream_url=url, model=payload["model"])

    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=payload, headers=headers)
    except Exception as exc:
        log_event("chat_fallback_failed", reason="upstream_request_failed", error=str(exc))
        return RouteResponse(
            ok=False,
            route="chat_fallback",
            executed=False,
            fallback_used=True,
            reply_text="Chat fallback gagal menghubungi bridge phase-1.",
            details={"reason": "upstream_request_failed", "error": str(exc), "delegated": True},
        )

    log_event("chat_fallback_upstream_response", status_code=response.status_code)

    if response.status_code == 401:
        return RouteResponse(
            ok=False,
            route="chat_fallback",
            executed=False,
            fallback_used=True,
            reply_text="Chat fallback gagal: autentikasi bridge phase-1 ditolak.",
            details={"reason": "upstream_auth_failed", "delegated": True, "status_code": 401},
        )

    if response.status_code >= 400:
        return RouteResponse(
            ok=False,
            route="chat_fallback",
            executed=False,
            fallback_used=True,
            reply_text="Chat fallback gagal di bridge phase-1.",
            details={"reason": "upstream_http_error", "delegated": True, "status_code": response.status_code},
        )

    try:
        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]
        content = message["content"]
        finish_reason = choice.get("finish_reason")
        model = data.get("model", payload["model"])
        upstream_object = data.get("object")
    except Exception as exc:
        log_event("chat_fallback_failed", reason="malformed_upstream_response", error=str(exc))
        return RouteResponse(
            ok=False,
            route="chat_fallback",
            executed=False,
            fallback_used=True,
            reply_text="Chat fallback gagal: response bridge phase-1 tidak valid.",
            details={"reason": "malformed_upstream_response", "delegated": True, "error": str(exc)},
        )

    log_event("chat_fallback_succeeded", model=model, finish_reason=finish_reason)
    return RouteResponse(
        ok=True,
        route="chat_fallback",
        executed=False,
        fallback_used=True,
        reply_text=content,
        details={
            "model": model,
            "provider": "phase1-bridge",
            "delegated": True,
            "upstream_object": upstream_object,
            "finish_reason": finish_reason,
        },
    )

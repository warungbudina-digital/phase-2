from __future__ import annotations

import json
import time
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response, StreamingResponse

from .fallback import (
    build_phase1_headers,
    check_router_auth,
    phase1_chat_completions_url,
)
from .logging_utils import log_event
from .models import RouteRequest, RouteResponse
from .routing import classify_request

app = FastAPI(title="glovewort-phase-2-router", version="0.2.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    log_event("request_validation_failed", errors=exc.errors())
    return JSONResponse(
        status_code=400,
        content={
            "ok": False,
            "route": "invalid",
            "executed": False,
            "fallback_used": False,
            "reply_text": "Request router tidak valid.",
            "details": {
                "reason": "request_validation_failed",
                "errors": exc.errors(),
            },
        },
    )


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}


@app.post("/route", response_model=RouteResponse)
def route(request: RouteRequest) -> RouteResponse:
    log_event(
        "route_request_received",
        channel=request.channel,
        chat_id=request.chat_id,
        message_text=request.message_text,
        metadata=request.metadata,
    )
    response = classify_request(request)
    log_event(
        "route_request_completed",
        route=response.route,
        executed=response.executed,
        fallback_used=response.fallback_used,
        ok=response.ok,
        details=response.details,
    )
    return response


def _normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type in {"text", "input_text", "output_text"} and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
            elif isinstance(item, str):
                parts.append(item)
        if parts:
            return "\n".join(parts)
    try:
        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)


def _extract_latest_user_text(payload: dict[str, Any]) -> str:
    messages = payload.get("messages") or []
    for msg in reversed(messages):
        if not isinstance(msg, dict):
            continue
        if msg.get("role") != "user":
            continue
        content = _normalize_content(msg.get("content"))
        if content.strip():
            return content.strip()
    return ""


def _make_route_request_from_chat(payload: dict[str, Any]) -> RouteRequest:
    latest_user = _extract_latest_user_text(payload)
    return RouteRequest(
        channel="openclaw",
        chat_id="openclaw-bridge",
        message_text=latest_user,
        metadata={"source": "chat_completions"},
    )


def _openai_completion_response(reply_text: str, model: str) -> dict[str, Any]:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": reply_text},
                "finish_reason": "stop",
            }
        ],
    }


def _openai_stream_chunk(content: str, model: str, request_id: str) -> dict[str, Any]:
    return {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
    }


@app.post("/v1/chat/completions", response_model=None)
async def chat_completions(request: Request, authorization: str | None = Header(default=None)) -> Response:
    auth_error = check_router_auth(authorization)
    if auth_error is not None:
        raise HTTPException(status_code=401, detail=auth_error)

    payload = await request.json()
    model = payload.get("model", "phase2-router")
    stream = bool(payload.get("stream", False))

    route_request = _make_route_request_from_chat(payload)
    log_event(
        "bridge_request_received",
        model=model,
        stream=stream,
        latest_user_message=route_request.message_text,
    )

    route_response = classify_request(route_request)
    log_event(
        "bridge_request_classified",
        route=route_response.route,
        executed=route_response.executed,
        fallback_used=route_response.fallback_used,
        ok=route_response.ok,
    )

    if route_response.route != "chat_fallback":
        if not stream:
            return JSONResponse(_openai_completion_response(route_response.reply_text, model))

        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        async def event_stream() -> Any:
            yield f"data: {json.dumps(_openai_stream_chunk(route_response.reply_text, model, request_id))}\n\n"
            final_chunk = {
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    upstream_url = phase1_chat_completions_url()
    if not upstream_url:
        return JSONResponse(
            status_code=502,
            content={"error": {"message": "PHASE1_BRIDGE_BASE_URL belum diatur", "type": "router_upstream_unavailable"}},
        )

    headers = build_phase1_headers(authorization)

    if not stream:
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                upstream = await client.post(upstream_url, json=payload, headers=headers)
        except Exception as exc:
            return JSONResponse(
                status_code=502,
                content={"error": {"message": str(exc), "type": "router_upstream_request_failed"}},
            )
        return Response(content=upstream.content, status_code=upstream.status_code, media_type=upstream.headers.get("content-type", "application/json"))

    async def proxy_stream() -> Any:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", upstream_url, json=payload, headers=headers) as upstream:
                if upstream.status_code >= 400:
                    body = await upstream.aread()
                    raise HTTPException(status_code=upstream.status_code, detail=body.decode("utf-8", errors="ignore"))
                async for chunk in upstream.aiter_bytes():
                    if chunk:
                        yield chunk

    return StreamingResponse(proxy_stream(), media_type="text/event-stream")

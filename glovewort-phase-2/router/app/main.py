from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .logging_utils import log_event
from .models import RouteRequest, RouteResponse
from .routing import classify_request

app = FastAPI(title="glovewort-phase-2-router", version="0.1.0")


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

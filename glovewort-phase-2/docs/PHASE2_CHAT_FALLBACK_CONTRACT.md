# Phase-2 Chat Fallback Delegation Contract

This document defines how `glovewort-phase-2` delegates non-deterministic requests to the phase-1 `glovewort` bridge.

---

## 1. Purpose

Phase-2 should execute deterministic commands directly.
If a message does not match a deterministic route, it must fall back to the phase-1 LLM bridge in a controlled, explicit way.

The fallback path is:

```text
phase-2 router -> phase-1 llm-bridge-api -> Ollama
```

---

## 2. When fallback is allowed

Fallback is allowed only when:

- the request is valid
- no deterministic route matched
- no block policy was triggered

Fallback must not be used to silently bypass a blocked command.

Example:

- `siapa kamu?` -> fallback allowed
- `rm -rf /` -> fallback not allowed, must remain blocked

---

## 3. Upstream endpoint

Phase-2 fallback target:

- `POST {PHASE1_BRIDGE_BASE_URL}/chat/completions` if the base URL already includes `/v1`
- concretely in current phase-1 config:
  - `http://llm-bridge-api:8000/v1/chat/completions`

Required env vars:

- `PHASE1_BRIDGE_BASE_URL`
- `PHASE1_BRIDGE_API_KEY`

---

## 4. Fallback request contract

Phase-2 sends a simplified Chat Completions request.

### Required request shape

```json
{
  "model": "qwen2.5-coder:3b-instruct",
  "messages": [
    {
      "role": "user",
      "content": "siapa kamu?"
    }
  ],
  "stream": false
}
```

### Rules

- use `stream: false` in phase-2A
- keep prompt minimal
- do not send phase-1/Telegram raw metadata dump unless explicitly needed
- do not send prior hallucinated execution text as context

---

## 5. Fallback response contract

Expected upstream response shape:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "qwen2.5-coder:3b-instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "..."
      },
      "finish_reason": "stop"
    }
  ]
}
```

Phase-2 must convert that into its own router response envelope.

---

## 6. Phase-2 router response for fallback

Example:

```json
{
  "ok": true,
  "route": "chat_fallback",
  "executed": false,
  "fallback_used": true,
  "reply_text": "Saya adalah ...",
  "details": {
    "model": "qwen2.5-coder:3b-instruct",
    "provider": "phase1-bridge",
    "delegated": true,
    "upstream_object": "chat.completion",
    "finish_reason": "stop"
  }
}
```

---

## 7. Failure behavior

### 7.1 Upstream unavailable

If the phase-1 bridge is unreachable:

- router returns `ok=false`
- route remains `chat_fallback`
- `fallback_used=true`
- reply text should clearly say fallback failed

### 7.2 Upstream malformed response

If bridge returns malformed payload:

- router returns `ok=false`
- details include `reason: malformed_upstream_response`

### 7.3 Auth failure

If bridge returns `401`:

- router returns `ok=false`
- details include `reason: upstream_auth_failed`

---

## 8. Logging requirements

Fallback path must log:

- fallback request issued
- upstream URL target (without secrets)
- upstream status code
- selected model
- fallback success/failure

---

## 9. Security rules

- do not log bridge API key
- do not include bearer token in structured logs
- do not pass blocked commands into fallback chat

---

## 10. Bottom line

Fallback exists to answer ordinary chat prompts.
It must never become a hidden path that turns blocked or deterministic commands back into model hallucinations.

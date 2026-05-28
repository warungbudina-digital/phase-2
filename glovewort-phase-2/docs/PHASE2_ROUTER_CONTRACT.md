# Phase-2 Router Request/Response Contract

This document defines the HTTP contract for the deterministic router service in `glovewort-phase-2`.

Scope:

- internal service contract only
- no handler implementation assumed yet
- phase-2A deterministic routing only

---

## 1. Purpose

The router must decide whether an incoming request should:

- execute a deterministic shell command
- read a file
- inspect Docker state
- or fall back to the phase-1 LLM bridge

The contract must make that decision explicit and machine-readable.

---

## 2. Core principles

### 2.1 Real execution must be distinguishable from chat fallback

A caller must always be able to tell whether a response came from:

- real command execution
- real file reading
- real docker inspection
- LLM chat fallback

### 2.2 Route decision must be explicit

The router must not return an ambiguous generic text blob.

Every response must include:

- selected route type
- whether execution actually happened
- whether fallback happened

### 2.3 Failure must be explicit

A rejected/blocked command must return a structured rejection.

---

## 3. Endpoints

## 3.1 `GET /healthz`

### Purpose

Service liveness endpoint.

### Response

```json
{
  "ok": true
}
```

### Notes

Phase-2A only requires process liveness here.
Later health may include dependency checks.

---

## 3.2 `POST /route`

### Purpose

Primary router entrypoint.

### Responsibility

- receive message text + metadata
- classify route
- optionally execute a real handler
- return structured result

---

## 4. Request contract

## 4.1 Request shape

```json
{
  "channel": "telegram",
  "chat_id": "843382635",
  "message_text": "jalankan pwd lalu balas hasilnya",
  "metadata": {
    "sender_id": "843382635",
    "sender_name": "OBC-crypto",
    "message_id": "177",
    "timestamp": "2026-05-20T00:45:00Z"
  }
}
```

## 4.2 Required fields

- `channel` (string)
- `chat_id` (string)
- `message_text` (string)

## 4.3 Optional fields

- `metadata` (object)
  - `sender_id`
  - `sender_name`
  - `message_id`
  - `timestamp`
  - future trace/debug fields

## 4.4 Validation rules

- `message_text` must be non-empty after trimming
- `channel` must be non-empty
- `chat_id` must be non-empty
- unknown metadata keys are allowed

---

## 5. Route types

The router must classify every accepted request into one of these route values.

- `command_exec`
- `file_read`
- `docker_inspect`
- `chat_fallback`
- `blocked`
- `invalid`

### Definitions

#### `command_exec`
Explicit shell command route.

#### `file_read`
File content read, optionally with later summary.

#### `docker_inspect`
Read-only Docker inspection.

#### `chat_fallback`
No deterministic command matched; send to LLM bridge.

#### `blocked`
A command pattern matched but was denied by safety policy.

#### `invalid`
Request payload itself invalid.

---

## 6. Common response envelope

Every `POST /route` response must follow this envelope.

```json
{
  "ok": true,
  "route": "command_exec",
  "executed": true,
  "fallback_used": false,
  "reply_text": "Perintah: pwd\nExit code: 0\nHasil:\n/home/warungbudina/glovewort",
  "details": {}
}
```

## 6.1 Common top-level fields

### `ok`
- boolean
- `true` when the request was processed successfully, even if command exit code != 0
- `false` when request handling failed at router level

### `route`
- enum from the route types above

### `executed`
- boolean
- `true` only if a real deterministic handler ran
- `false` for fallback chat, blocked, or invalid requests

### `fallback_used`
- boolean
- `true` only if request was delegated to chat fallback

### `reply_text`
- string
- text safe to send back to Telegram

### `details`
- object
- route-specific structured payload

---

## 7. Route-specific response contracts

## 7.1 `command_exec`

### Example response

```json
{
  "ok": true,
  "route": "command_exec",
  "executed": true,
  "fallback_used": false,
  "reply_text": "Perintah: pwd\nExit code: 0\nHasil:\n/home/warungbudina/glovewort",
  "details": {
    "command": "pwd",
    "exit_code": 0,
    "stdout": "/home/warungbudina/glovewort\n",
    "stderr": "",
    "duration_ms": 12,
    "truncated": false
  }
}
```

### Required `details` keys

- `command`
- `exit_code`
- `stdout`
- `stderr`
- `duration_ms`
- `truncated`

### Notes

- non-zero command exit code does not require `ok=false`
- if command was executed safely, `ok` may still be `true`
- caller should inspect `details.exit_code`

---

## 7.2 `file_read`

### Example response

```json
{
  "ok": true,
  "route": "file_read",
  "executed": true,
  "fallback_used": false,
  "reply_text": "README.md berhasil dibaca. Ringkasan: repositori ini adalah baseline phase-1 untuk OpenClaw + bridge + Ollama.",
  "details": {
    "path": "README.md",
    "mode": "read_and_summarize",
    "bytes_read": 1820,
    "truncated": false,
    "summary_used": true,
    "raw_excerpt": "# glovewort..."
  }
}
```

### Required `details` keys

- `path`
- `mode`
- `bytes_read`
- `truncated`
- `summary_used`

### Optional `details` keys

- `raw_excerpt`
- `summary_model`

---

## 7.3 `docker_inspect`

### Example response

```json
{
  "ok": true,
  "route": "docker_inspect",
  "executed": true,
  "fallback_used": false,
  "reply_text": "Perintah: docker ps\nExit code: 0\nHasil:\nCONTAINER ID ...",
  "details": {
    "command": "docker ps",
    "exit_code": 0,
    "stdout": "CONTAINER ID ...\n",
    "stderr": "",
    "duration_ms": 48,
    "truncated": false
  }
}
```

### Notes

This is structurally similar to `command_exec`, but route value remains distinct for auditability.

---

## 7.4 `chat_fallback`

### Example response

```json
{
  "ok": true,
  "route": "chat_fallback",
  "executed": false,
  "fallback_used": true,
  "reply_text": "Saya adalah glovewort phase-1 assistant...",
  "details": {
    "model": "qwen2.5-coder:3b-instruct",
    "provider": "phase1-bridge",
    "delegated": true
  }
}
```

### Required `details` keys

- `model`
- `provider`
- `delegated`

---

## 7.5 `blocked`

### Example response

```json
{
  "ok": false,
  "route": "blocked",
  "executed": false,
  "fallback_used": false,
  "reply_text": "Perintah ditolak oleh kebijakan keamanan phase-2.",
  "details": {
    "reason": "command_not_allowed",
    "matched_command": "rm -rf /",
    "policy": "phase2A-safe-allowlist"
  }
}
```

### Required `details` keys

- `reason`
- `policy`

### Optional `details` keys

- `matched_command`
- `matched_path`

---

## 7.6 `invalid`

### Example response

```json
{
  "ok": false,
  "route": "invalid",
  "executed": false,
  "fallback_used": false,
  "reply_text": "Request router tidak valid.",
  "details": {
    "reason": "missing_message_text"
  }
}
```

---

## 8. HTTP status policy

## 8.1 `200 OK`

Use when:

- request parsed successfully
- route decision made successfully
- execution completed or fallback completed
- blocked command intentionally rejected at business-logic level

This includes:

- successful command execution
- command execution with non-zero exit code
- blocked requests
- chat fallback success

## 8.2 `400 Bad Request`

Use when:

- request body is malformed
- required fields missing or wrong type

## 8.3 `500 Internal Server Error`

Use when:

- router internal exception occurs
- handler crashes unexpectedly
- fallback bridge call fails in an unhandled way

---

## 9. Telegram reply contract

`reply_text` must always be safe to send directly to Telegram.

Requirements:

- plain text
- concise enough for Telegram message limits
- no assumption of markdown tables

If raw output is too large:

- truncate
- indicate truncation in `details.truncated`
- optionally summarize

---

## 10. Safety contract

The request/response contract alone is not sufficient. Each route must pass safety enforcement.

### `command_exec`
Must pass:

- command allowlist
- timeout policy
- no destructive operations

### `file_read`
Must pass:

- allowed root check
- normalized path check
- text-file policy

### `docker_inspect`
Must pass:

- read-only docker command policy

If safety fails, route must become:

- `blocked`

---

## 11. Logging contract

Each `/route` request should produce structured logs with at least:

- input summary
- route decision
- matched rule
- handler result
- exit code if executed
- fallback reason if delegated to chat

This is a runtime requirement, but it is part of the contract because observability is mandatory for trust.

---

## 12. Minimal examples

## 12.1 Example: `jalankan pwd`

Request:

```json
{
  "channel": "telegram",
  "chat_id": "843382635",
  "message_text": "jalankan pwd"
}
```

Response:

```json
{
  "ok": true,
  "route": "command_exec",
  "executed": true,
  "fallback_used": false,
  "reply_text": "Perintah: pwd\nExit code: 0\nHasil:\n/home/warungbudina/glovewort",
  "details": {
    "command": "pwd",
    "exit_code": 0,
    "stdout": "/home/warungbudina/glovewort\n",
    "stderr": "",
    "duration_ms": 8,
    "truncated": false
  }
}
```

## 12.2 Example: `baca README.md lalu ringkas`

Request:

```json
{
  "channel": "telegram",
  "chat_id": "843382635",
  "message_text": "baca README.md lalu ringkas"
}
```

Response:

```json
{
  "ok": true,
  "route": "file_read",
  "executed": true,
  "fallback_used": false,
  "reply_text": "README.md berhasil dibaca. Ringkasan: ...",
  "details": {
    "path": "README.md",
    "mode": "read_and_summarize",
    "bytes_read": 1820,
    "truncated": false,
    "summary_used": true
  }
}
```

## 12.3 Example: normal question

Request:

```json
{
  "channel": "telegram",
  "chat_id": "843382635",
  "message_text": "siapa kamu?"
}
```

Response:

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
    "delegated": true
  }
}
```

---

## 13. Bottom line

This contract exists to guarantee that phase-2 can no longer blur the line between:

- **real execution**
- and **model-generated text pretending to be execution**

If the response does not explicitly indicate route and execution status, the router is not behaving correctly.

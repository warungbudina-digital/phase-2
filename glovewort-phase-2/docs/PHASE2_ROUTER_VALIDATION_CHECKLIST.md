# Phase-2 Router Validation Checklist

This checklist defines the minimum validation gates before phase-2 router behavior can be trusted.

Scope:

- request validation
- route classification integrity
- deterministic execution boundaries
- fallback clarity
- Telegram-safe output contract

---

## 1. Request validation

### Payload shape

- [ ] rejects missing `channel`
- [ ] rejects missing `chat_id`
- [ ] rejects missing `message_text`
- [ ] rejects empty `message_text` after trimming
- [ ] accepts extra `metadata` keys without crashing

### HTTP behavior

- [ ] malformed JSON returns `400`
- [ ] wrong field types return `400`
- [ ] valid requests return `200`

---

## 2. Route classification

### Deterministic execution routes

- [ ] `jalankan pwd` -> `command_exec`
- [ ] `jalankan ls` -> `command_exec`
- [ ] `docker ps` -> `docker_inspect`
- [ ] `docker compose ps` -> `docker_inspect`
- [ ] `baca README.md` -> `file_read`
- [ ] `baca README.md lalu ringkas` -> `file_read`

### Fallback route

- [ ] `siapa kamu?` -> `chat_fallback`
- [ ] non-command text does not accidentally route to `command_exec`

### Invalid or blocked cases

- [ ] unsafe command pattern becomes `blocked`
- [ ] structurally invalid request becomes `invalid`

---

## 3. Safety policy validation

### Shell safety

- [ ] `pwd` allowed
- [ ] `ls` allowed
- [ ] `whoami` allowed
- [ ] `rm -rf /` blocked
- [ ] `shutdown now` blocked
- [ ] `docker stop ...` blocked in phase-2A

### File safety

- [ ] allowed workspace path accepted
- [ ] path traversal attempts rejected
- [ ] disallowed secret paths rejected

### Docker safety

- [ ] `docker ps` allowed
- [ ] `docker images` allowed
- [ ] destructive docker operations blocked

---

## 4. Response contract validation

### Common envelope

- [ ] every response includes `ok`
- [ ] every response includes `route`
- [ ] every response includes `executed`
- [ ] every response includes `fallback_used`
- [ ] every response includes `reply_text`
- [ ] every response includes `details`

### Deterministic execution response

- [ ] `command_exec` includes `command`
- [ ] `command_exec` includes `exit_code`
- [ ] `command_exec` includes `stdout`
- [ ] `command_exec` includes `stderr`
- [ ] `command_exec` includes `duration_ms`
- [ ] `command_exec` includes `truncated`

### File read response

- [ ] `file_read` includes `path`
- [ ] `file_read` includes `mode`
- [ ] `file_read` includes `bytes_read`
- [ ] `file_read` includes `summary_used`

### Fallback response

- [ ] `chat_fallback` includes provider/model identity
- [ ] `executed=false` for fallback responses

### Blocked response

- [ ] blocked responses explain reason and policy

---

## 5. Telegram reply safety

- [ ] reply text is plain-text friendly
- [ ] long output is truncated safely
- [ ] truncation is reflected in structured `details`
- [ ] output avoids fabricated command results

---

## 6. Observability

- [ ] router logs incoming request summary
- [ ] router logs chosen route
- [ ] router logs matched rule
- [ ] router logs handler result
- [ ] router logs fallback reason when chat path used
- [ ] router logs block reason when command denied

---

## 7. Integration checkpoints

### Router standalone

- [ ] `/healthz` returns `200`
- [ ] `/route` validates payloads correctly

### Router + phase-1 bridge

- [ ] chat fallback reaches phase-1 bridge successfully
- [ ] deterministic execution does not invoke chat fallback unnecessarily

---

## 8. Anti-hallucination criteria

These are non-negotiable.

- [ ] `jalankan pwd` returns real cwd, not model-fabricated text
- [ ] `docker ps` returns real container IDs
- [ ] `baca README.md` reflects actual file content
- [ ] deterministic routes never rely on LLM imagination for primary result

---

## 9. Phase-2A exit criteria

Phase-2A is considered ready only when:

- [ ] request validation is stable
- [ ] route classification is stable
- [ ] safety policy is enforceable
- [ ] response envelope is consistent
- [ ] deterministic routes return real grounded outputs
- [ ] fallback chat remains available for non-command prompts

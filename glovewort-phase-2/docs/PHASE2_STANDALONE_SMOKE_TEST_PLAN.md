# Phase-2 Standalone Smoke-Test Plan

This plan validates `glovewort-phase-2` as an independent router service before wiring it into Telegram/OpenClaw ingress.

Scope:

- deterministic-router only
- local request validation
- route classification
- minimal deterministic handlers
- fallback call to phase-1 bridge

---

## 1. Preconditions

Before running these tests, ensure:

- phase-1 `glovewort` stack is running if fallback tests are included
- Docker socket is available on the host
- router workspace mount points to a real repo or test workspace

Recommended:

- test from the `glovewort-phase-2` repo root

---

## 2. Prepare env

```bash
cd ~/glovewort-phase-2
cp .env.example .env
```

Review and set at minimum:

- `PHASE1_BRIDGE_BASE_URL`
- `PHASE1_BRIDGE_API_KEY`
- `ROUTER_WORKSPACE_HOST_PATH`
- `ROUTER_WORKSPACE_ROOT`

Example values:

```env
PHASE1_BRIDGE_BASE_URL=http://host.docker.internal:8000/v1
PHASE1_BRIDGE_API_KEY=<bridge-key>
ROUTER_WORKSPACE_HOST_PATH=/home/warungbudina/glovewort
ROUTER_WORKSPACE_ROOT=/workspace
```

If phase-1 bridge is in another compose stack on the same host, using `host.docker.internal` is acceptable for initial standalone smoke testing.

---

## 3. Validate compose rendering

```bash
cd ~/glovewort-phase-2
docker compose config >/tmp/glovewort-phase2.compose.rendered.yaml
```

Check specifically:

- workspace bind mount path is correct
- Docker socket is mounted read-only
- `PHASE1_BRIDGE_BASE_URL` is present

---

## 4. Build router

```bash
cd ~/glovewort-phase-2
docker compose build 2>&1 | tee /tmp/glovewort-phase2-build.log
```

Success criteria:

- image builds without dependency errors
- `httpx` is installed
- app imports resolve correctly

---

## 5. Start router

```bash
cd ~/glovewort-phase-2
docker compose up -d 2>&1 | tee /tmp/glovewort-phase2-up.log
```

Check:

```bash
docker compose ps -a
docker compose logs --tail 120 deterministic-router
```

Success criteria:

- `deterministic-router` is `Up`
- healthcheck becomes `healthy`

---

## 6. Health endpoint test

```bash
curl -sS http://127.0.0.1:8090/healthz
```

Expected:

```json
{"ok": true}
```

---

## 7. Request validation tests

### 7.1 Missing required fields

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{}'
```

Expected:

- HTTP `400`
- `route: invalid`
- structured validation errors present

### 7.2 Empty message text

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"   "}'
```

Expected:

- HTTP `400`
- `route: invalid`

---

## 8. Deterministic command tests

### 8.1 `pwd`

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"jalankan pwd"}'
```

Expected:

- `route: command_exec`
- `executed: true`
- `details.command: pwd`
- real working directory in `stdout`

### 8.2 `whoami`

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"jalankan whoami"}'
```

Expected:

- `route: command_exec`
- `executed: true`
- real username in `stdout`

### 8.3 blocked command

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"jalankan rm -rf /"}'
```

Expected:

- `route: blocked`
- `executed: false`
- policy reason present

---

## 9. File-read tests

### 9.1 read README

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"baca README.md"}'
```

Expected:

- `route: file_read`
- `executed: true`
- actual README content excerpt returned

### 9.2 read + summarize stub

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"baca README.md lalu ringkas"}'
```

Expected:

- `route: file_read`
- `mode: read_and_summarize_stub`
- actual excerpt included
- no hallucinated summary

### 9.3 path traversal blocked

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"baca ../../etc/passwd"}'
```

Expected:

- `route: blocked`
- path root policy reason present

---

## 10. Docker inspect tests

### 10.1 docker ps

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"docker ps"}'
```

Expected:

- `route: docker_inspect`
- `executed: true`
- real container IDs in output

### 10.2 docker compose ps

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"docker compose ps"}'
```

Expected:

- `route: docker_inspect`
- `executed: true`

---

## 11. Fallback chat tests

### 11.1 normal chat question

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"siapa kamu?"}'
```

Expected:

- `route: chat_fallback`
- `fallback_used: true`
- `executed: false`
- reply text from phase-1 bridge

### 11.2 blocked command must not fallback

```bash
curl -sS -X POST http://127.0.0.1:8090/route \
  -H 'Content-Type: application/json' \
  -d '{"channel":"telegram","chat_id":"843382635","message_text":"jalankan docker stop ollama-brain"}'
```

Expected:

- `route: blocked`
- not `chat_fallback`

---

## 12. Logging checks

After any test, inspect:

```bash
docker compose logs --tail 200 deterministic-router
```

Look for:

- `route_request_received`
- `route_request_completed`
- `command_executed`
- `file_read`
- `command_blocked`
- `chat_fallback_started`
- `chat_fallback_succeeded`
- `chat_fallback_failed`

Success criteria:

- logs clearly distinguish deterministic execution from fallback chat
- no fabricated execution path appears without a matching handler log

---

## 13. Minimum smoke-test pass criteria

Phase-2 standalone smoke test passes only if:

- router health is green
- request validation rejects bad input correctly
- `pwd` executes for real
- `README.md` is read for real
- `docker ps` returns real container output
- blocked commands remain blocked
- ordinary chat successfully falls back to phase-1 bridge
- logs clearly show route decisions

# Phase-2 Router File-by-File Specification

This document defines the target file layout for `glovewort-phase-2` after the handler-family refactor.

---

## 1. Target structure

```text
router/
  Dockerfile
  requirements.txt
  app/
    main.py
    models.py
    routing.py
    safety.py
    formatters.py
    logging_utils.py
    fallback.py
    handlers/
      __init__.py
      local_exec.py
      file_read.py
      docker_inspect.py
      phase1_fallback.py
      internal_api.py
```

---

## 2. Root runtime files

### `router/Dockerfile`
Purpose:
- build the standalone phase-2 router container

Must include:
- Python runtime
- app code copy
- dependency install
- health-capable startup command

### `router/requirements.txt`
Purpose:
- freeze runtime dependencies

Phase-2A expected packages:
- `fastapi`
- `uvicorn`
- `pydantic`
- `httpx`

---

## 3. Core app files

### `router/app/main.py`
Purpose:
- FastAPI ingress only

Owns:
- `GET /healthz`
- `POST /route`
- request validation failure mapping
- top-level structured request lifecycle logging

Must not own:
- route classification rules
- command execution logic
- file IO logic
- Docker inspection logic

### `router/app/models.py`
Purpose:
- request/response schema contract

Owns:
- `RouteRequest`
- `RouteResponse`
- route literals / enums
- field validation for channel/chat/message text

### `router/app/routing.py`
Purpose:
- deterministic route classifier and dispatcher

Owns:
- message-text classification
- mapping route type to handler family
- explicit decision boundary between deterministic routes and fallback

Must not own:
- shell execution
- file reads
- Docker command implementation
- outbound fallback HTTP client details

### `router/app/safety.py`
Purpose:
- shared policy enforcement

Owns:
- command allowlist
- blocked substring rules
- workspace path resolution
- text-file checks
- Docker read-only rules
- timeout/output caps

### `router/app/formatters.py`
Purpose:
- normalize handler results into Telegram-safe reply text

Owns:
- truncation policy for displayed output
- consistent reply formatting helpers
- optional summary block formatting

### `router/app/logging_utils.py`
Purpose:
- structured router event logging

Owns:
- event logger helper
- log level normalization
- lightweight field truncation

### `router/app/fallback.py`
Purpose:
- shared fallback helper layer for phase-1 bridge calls

Owns:
- base URL normalization
- auth header construction
- shared HTTP client helper(s) if needed

Design note:
- if fallback logic becomes family-specific only, this file may shrink into helper utilities or disappear later

---

## 4. Handler family files

### `router/app/handlers/__init__.py`
Purpose:
- mark handler family package
- optional stable re-exports later

### `router/app/handlers/local_exec.py`
Purpose:
- own deterministic local shell execution

Phase-2A scope:
- `pwd`
- `ls`
- `ls -la`
- `whoami`
- `df -h`

Must use:
- `safety.py` for allow/deny
- `logging_utils.py` for audit trail
- `formatters.py` for output shaping

### `router/app/handlers/file_read.py`
Purpose:
- own grounded file reading

Phase-2A scope:
- `baca <path>`
- `read <path>`
- `baca <path> lalu ringkas`

Must use:
- workspace path guard from `safety.py`
- text-file checks from `safety.py`
- summary formatting from `formatters.py`

### `router/app/handlers/docker_inspect.py`
Purpose:
- own read-only Docker inspection

Phase-2A scope:
- `docker ps`
- `docker compose ps`
- `docker images`
- `cek container`

Must use:
- Docker allow rules from `safety.py`
- deterministic formatting helpers

### `router/app/handlers/phase1_fallback.py`
Purpose:
- own non-deterministic chat delegation to phase-1 bridge

Phase-2A scope:
- general chat questions
- explanation/help requests
- summary fallback for non-deterministic asks

Must use:
- shared bridge helper(s) from `fallback.py`
- structured success/failure logging

Hard rule:
- must not receive blocked deterministic commands as silent fallback

### `router/app/handlers/internal_api.py`
Purpose:
- reserved extension point for phase-2B internal gloves

Future scope:
- same-host helper APIs
- same-network service tools
- internal-only analyzer endpoints

Not required for phase-2A runtime completion.

---

## 5. Transitional files and migration rule

### Transitional current-state files
Current scaffold may still contain implementation in:
- `router/app/handlers.py`
- `router/app/fallback.py`

Migration rule:
- move execution logic out of `handlers.py` into family modules
- keep `routing.py` stable while swapping imports behind it
- remove `handlers.py` only after family modules cover all phase-2A routes

This avoids a risky all-at-once rewrite.

---

## 6. Refactor sequence

Recommended order:

1. create `handlers/` package
2. move local exec logic into `handlers/local_exec.py`
3. move file read logic into `handlers/file_read.py`
4. move Docker inspect logic into `handlers/docker_inspect.py`
5. move fallback delegation into `handlers/phase1_fallback.py`
6. reduce `handlers.py` into shim or remove it
7. update smoke tests against family-based imports

This is the file-by-file target the repo should follow before heavier phase-2 implementation.

# Phase-2 Handler Family Structure

This document freezes the target handler layout for `glovewort-phase-2`.

The objective is simple:
- keep `routing.py` thin
- keep policy in `safety.py`
- move execution into explicit handler families
- keep fallback separate from deterministic execution

---

## 1. Target directory layout

```text
router/app/
  main.py
  models.py
  routing.py
  safety.py
  formatters.py
  logging_utils.py
  fallback.py                # transitional shared helper, optional long-term
  handlers/
    __init__.py
    local_exec.py
    file_read.py
    docker_inspect.py
    phase1_fallback.py
    internal_api.py
```

---

## 2. Responsibility split

### `routing.py`
Only decides route family.

It may:
- classify message text
- call one handler family entrypoint
- return a normalized `RouteResponse`

It must not:
- run shell commands directly
- open files directly
- call Docker directly
- embed large formatting logic
- embed fallback HTTP client logic

### `safety.py`
Shared policy authority.

It owns:
- command allowlist
- blocked patterns
- workspace path resolution
- text-file validation
- docker read-only guardrails
- timeout and output caps

### `handlers/*`
Each family owns one execution surface.

This keeps:
- logs cleaner
- tests narrower
- future refactors safer
- merge conflicts lower

---

## 3. Handler families

### `handlers/local_exec.py`
Owns deterministic local command execution.

Phase-2A scope:
- `pwd`
- `ls`
- `ls -la`
- `whoami`
- `df -h`

Hard rule:
- only read-only / observational commands
- no install, delete, kill, prune, or network-heavy commands

### `handlers/file_read.py`
Owns grounded file reads under workspace root.

Phase-2A scope:
- `baca <path>`
- `read <path>`
- `baca <path> lalu ringkas`

Hard rule:
- path must resolve inside workspace root
- binary files blocked
- summary path must remain grounded to actual file content

### `handlers/docker_inspect.py`
Owns read-only Docker inspection.

Phase-2A scope:
- `docker ps`
- `docker compose ps`
- `docker images`
- `cek container`

Hard rule:
- no `docker rm`, `docker stop`, `docker kill`, `docker system prune`

### `handlers/phase1_fallback.py`
Owns chat fallback delegation.

Phase-2A scope:
- non-deterministic chat queries
- summary/help/explanation fallback

Hard rule:
- blocked deterministic commands must not silently fall back here
- fallback is for chat, not for bypassing policy

### `handlers/internal_api.py`
Reserved for phase-2B.

Future scope:
- same-host/same-network helper APIs
- analyzer services
- other internal gloves

Not required for phase-2A completion.

---

## 4. Execution boundary

The family boundary should look like this:

```text
main.py
  -> routing.py
    -> handlers/<family>.py
      -> safety.py / formatters.py / logging_utils.py / fallback.py
```

This gives a stable chain:
- ingress
- route decision
- guarded execution
- structured logging
- normalized reply

---

## 5. Transitional note

Current scaffold may still contain:
- `handlers.py`
- `fallback.py`

That is acceptable only as a migration state.

Target steady state:
- real execution lives in `handlers/`
- `handlers.py` should eventually disappear or become a compatibility shim
- `fallback.py` may remain only if shared helper code is still useful

---

## 6. Why this is the correct shape

Compared with one large `handlers.py`, this structure gives:
- clearer ownership per execution surface
- smaller review units
- easier safety audits
- cleaner route-level tests
- easier extension into internal gloves later

This is the right base for deterministic routing.

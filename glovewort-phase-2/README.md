# glovewort-phase-2

Phase-2 repository for the deterministic command router that sits in front of the phase-1 `glovewort` base.

## Purpose

This repo exists to turn the current `glovewort` text-assistant baseline into a deterministic executor for a bounded command surface.

Phase-2 is responsible for:

- explicit command routing
- safe command execution
- file-read routing
- docker inspection routing
- fallback chat routing to the phase-1 LLM bridge

It is **not** the place for:

- OpenClaw 2026.4.2 base image design
- Ollama bridge baseline
- generic Telegram assistant baseline

Those stay in the phase-1 reusable repo:

- `glovewort`

## Status

Design-first only.
No runtime implementation should be assumed yet.

## Expected topology

```text
Telegram -> OpenClaw gateway -> deterministic-router ->
  (a) exec/read/docker handlers
  (b) or glovewort llm-bridge-api -> Ollama
```

## Initial contents

- `docs/PHASE2_DETERMINISTIC_ROUTER_ARCHITECTURE.md`
- `docs/PHASE2_ROUTER_FILE_SPEC.md`
- `docs/PHASE2_ROUTER_RUNTIME_PLAN.md`
- `router/` scaffold only


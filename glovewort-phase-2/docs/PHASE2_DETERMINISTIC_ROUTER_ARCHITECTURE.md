# Phase-2 Deterministic Router Architecture

This repository owns the deterministic routing layer.

## Design rule

- router-first
- model-second

If a message matches a deterministic execution pattern, it must execute via a real handler.
If it does not match, it may fall back to the phase-1 LLM bridge.

## Route types

- `command_exec`
- `file_read`
- `docker_inspect`
- `chat_fallback`

## Initial goal

Provide trustworthy execution for bounded commands such as:

- `jalankan pwd`
- `jalankan ls`
- `baca README.md`
- `docker ps`

without relying on the LLM to simulate tool output.

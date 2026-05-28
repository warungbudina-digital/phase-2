# Phase-2 Router Runtime Plan

## Objective

Move from design docs to a minimal runnable router without mixing in phase-1 bridge concerns.

## Order

1. Scaffold router image and app package.
2. Implement `/healthz`.
3. Implement deterministic route classification only.
4. Implement safe `pwd`, `ls`, `whoami` handlers.
5. Implement file-read handler with path restrictions.
6. Implement docker inspect read-only handler.
7. Add fallback chat delegation to phase-1 bridge.
8. Add structured logs and validation tests.

## Non-goals for first runtime slice

- destructive commands
- file writes
- autonomous remediation
- browser automation

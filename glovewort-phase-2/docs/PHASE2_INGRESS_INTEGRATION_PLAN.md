# Phase-2 Ingress Integration Plan

This document defines the minimal wiring required to place `glovewort-phase-2` in front of phase-1 OpenClaw.

---

## 1. Goal

Change the live path from:

```text
Telegram -> OpenClaw -> llm-bridge-api -> Ollama
```

into:

```text
Telegram -> OpenClaw -> deterministic-router ->
  (a) deterministic exec/read/docker
  (b) or llm-bridge-api -> Ollama
```

---

## 2. Required integration changes

### Phase-2
- join the same Docker network as phase-1 (`brain_hand_net`)
- expose `/v1/chat/completions`
- accept the same bridge auth key OpenClaw already uses
- forward fallback requests to `llm-bridge-api`

### Phase-1
- keep Telegram ingress in OpenClaw
- change `BRIDGE_BASE_URL` for `openclaw-gateway` from `http://llm-bridge-api:8000/v1` to `http://deterministic-router:8090/v1`
- keep `llm-bridge-api` running as the fallback model service behind the router

---

## 3. Environment contract

### Phase-2 `.env`
- `PHASE1_BRIDGE_BASE_URL=http://llm-bridge-api:8000/v1`
- `PHASE1_BRIDGE_API_KEY=<same bridge key used by phase-1 bridge>`
- `ROUTER_BRIDGE_API_KEY=<same key OpenClaw sends when calling the router>`
- `BRAIN_HAND_NETWORK=brain_hand_net`

### Phase-1 `.env`
- `BRIDGE_BASE_URL=http://deterministic-router:8090/v1`
- `BRIDGE_API_KEY=<same key as ROUTER_BRIDGE_API_KEY>`

Using one shared key is acceptable for phase-2A/2B integration simplicity.

---

## 4. Verification sequence

1. phase-2 container can resolve `llm-bridge-api`
2. phase-2 `/route` deterministic tests pass
3. phase-2 `POST /v1/chat/completions` deterministic test passes
4. phase-2 `POST /v1/chat/completions` fallback test passes
5. phase-1 `openclaw-gateway` points to `deterministic-router`
6. Telegram request that contains `docker ps` executes via deterministic route
7. Telegram chat request that contains `siapa kamu?` falls back to phase-1 bridge

---

## 5. Non-goals for this step

- replacing Telegram ingress entirely
- removing OpenClaw from the path
- full tool-calling semantics inside OpenClaw
- remote internet gloves

This step is only about placing the deterministic router between OpenClaw and the model bridge.

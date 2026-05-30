# Phase-2 Internal Completion Checklist

This checklist defines when `glovewort-phase-2` is considered internally complete enough for Telegram/OpenClaw wiring.

Internal completion does **not** mean production integration.
It means the standalone router service is technically coherent and its bounded execution surface works as designed.

---

## 1. Service runtime

- [x] container builds successfully
- [x] `GET /healthz` returns success
- [x] structured logs are emitted
- [x] request validation failures return `400` with `route=invalid`

---

## 2. Deterministic local exec

- [x] `jalankan pwd` executes for real
- [x] `jalankan whoami` executes for real
- [x] blocked commands return `route=blocked`
- [x] natural-language variants like `tolong jalankan pwd` are classified into deterministic exec

---

## 3. File read route

- [x] `baca README.md` reads a real file
- [x] `baca README.md lalu ringkas` stays grounded to real file content
- [x] path traversal is blocked
- [x] natural-language variants like `tolong baca README.md` are classified into file-read route

---

## 4. Docker inspect route

- [x] `docker compose ps` executes for real
- [x] `docker ps` is mapped deterministically to compose-scoped inspection in phase-2A
- [x] `cek container` is mapped deterministically to compose-scoped inspection
- [x] mutating Docker actions remain blocked

---

## 5. Chat fallback

- [x] fallback contract exists
- [x] fallback code path exists
- [ ] fallback connectivity to phase-1 bridge is verified in the target environment
- [ ] fallback returns successful model output from target environment

---

## 6. Internal-only boundary

- [x] phase-2 works as a standalone HTTP service
- [x] no Telegram wiring is required for internal completion
- [x] no OpenClaw ingress changes are required for internal completion

---

## 7. Ready-to-integrate definition

Phase-2 internal is ready for ingress integration when:

1. deterministic exec works
2. deterministic file read works
3. deterministic docker inspect works
4. fallback connectivity is verified
5. route logs are readable enough for debugging

At that point, the next phase is ingress wiring, not more internal router speculation.

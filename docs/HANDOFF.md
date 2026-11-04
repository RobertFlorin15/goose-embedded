# Handoff

2026-11-05. Completed scalar-v0 runtime host gate after validator commit 6250b4a.
**No Xtensa/ESP-IDF build, simulator, hardware result or HAL exists yet.**

Recover AGENTS.md -> PROJECT_STATE.md -> project skill -> Git/source/evidence.
Branch main, no remote; previous implementation 6250b4a. Current runtime checkpoint
is the commit containing this handoff (`git log -1 --oneline` resolves exact ID).
Clean on recovery; task changes intended to be committed together, leaving no
uncommitted changes. Verify git status rather than trust documentation.

Implementation: tracked patches/goose/0001 plus 0002 and their manifests.
Preparation defaults to both; --validator-only reproduces the historical first
stage. Fresh sources are built from clean pin 335fddc13dc74666398ffe160ec8a8f2958329d0.
Reference .cache/goose is unchanged. Current development tree
.cache/goose-scalar-runtime and binary build/goose-scalar-runtime/goose match the
patch chain (version 335fddc+scalar-v0-runtime, desktop runtime d22ae129d92b).
Do not rely on cache edits; rebuild from tracked artifacts if absent.

Verified: 560 runtime commands (179 expected failures), including 496 arithmetic
cases at -O0/-O2; current validator 235 commands plus nested desktop 19; old
validator-only mode 237; normal desktop runtime probe 32; scoped upstream CLI/
JSON suites. Native and generic i386 freestanding objects only need the panic
hook; 11 phases/level have zero selected heap/VM/signal/pthread calls. No LTO or
section GC used. Runtime embedding generator is byte-idempotent; desktop runtime
C output is byte-identical to the prior compiler. Strict host C syntax and
patch/source checks pass. [SCALAR_RUNTIME.md](../research/SCALAR_RUNTIME.md) has
commands, counts, scope and corrections; tracked results preserve reviewed evidence.

Contract: profile selects isolated canonical runtime_scalar.h and no desktop
sections; init accepts only 0/NULL, sets ready, exit clears ready. Repeated/cold
calls follow SCALAR_PROFILE.md. Invalid calls/overflow/unreachable paths invoke
required noreturn ge_scalar_v0_panic_v1(message,file,line), ABI 1. No default hook.
The Linux test hook uses write/_Exit; a real ESP-IDF hook must be implemented.
Single serial normal-task caller only; no reentrancy/ISR/concurrency support.
Compiler-internal unused gs_globals_main is synthetic, not a user-global feature.
Generic i386 compilation is not Xtensa evidence; no target memory/stack budget.

Exact next steps:
1. Inventory installed SDK/toolchain availability. Consult official current
   Espressif docs/releases and select a concrete ESP-IDF/toolchain pin.
2. Establish project-local reproducible setup and build an unchanged official
   ESP32-S3 baseline, recording versions, commands, logs and target settings.
3. Only then compile scalar leaf C as a component; implement the required panic
   hook and app_main C adapter; inspect Xtensa symbols/assembly/map and task stack
   assumptions. No board operation or HAL work until preceding gates pass.
4. Obtain board details and explicit authorization before flash/serial operations.

Commands:
```sh
git status --short --branch
git log -3 --oneline
python3 tools/test_scalar_runtime.py --compiler build/goose-scalar-runtime/goose
python3 tools/test_scalar_validator.py --compiler build/goose-scalar-runtime/goose
```
If missing, follow tools/README.md; preparation refuses an existing destination.
Blockers: no project SDK pin/baseline, target adapter/ABI/memory proof, board data,
full upstream suite, or release license inventory. Grapify unavailable in prior
check. Sol/medium suits SDK setup; use Astra/high for ABI/toolchain blockers.
[Architecture](ARCHITECTURE.md), [profile](SCALAR_PROFILE.md), [roadmap](ROADMAP.md).

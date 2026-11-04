# Handoff

2026-11-04. User task complete: opt-in scalar-v0 compiler validator and rejection
tests, **before** runtime startup adaptation. M2a remains in progress; no target
runtime, Xtensa build, simulator, HAL or hardware run exists.

Recover via AGENTS.md, PROJECT_STATE.md, project skill and Git/source checks.
Branch main; prior verified checkpoint fcc2689. Current implementation is the
commit containing this handoff (`git log -1 --oneline` resolves its exact ID).
Clean on recovery; task changes intended to be committed together; verify
`git status --short`. No remote. Cache/build directories are ignored/disposable.

Durable implementation: patches/goose/0001-scalar-v0-validator.patch and its
manifest/license/provenance README; preparation helper extracts clean pin
335fddc13dc74666398ffe160ec8a8f2958329d0, applies patch and verifies file hashes.
Keep .cache/goose clean. Development patched tree .cache/goose-scalar and binary
build/goose-scalar/goose match the patch; rebuild if absent using tools/README.md.
Never rely on undocumented edits in that ignored copy.

Verified result: 237 validator/regression commands pass (209 expected failures);
46 source cases plus sidecar at -O0/-O2; forced overflow checks for add/sub/mul/
neg; accepted scalar semantics/restart; CLI/action/alias/staging/preparation
checks. Nested 19-command desktop host probe and scoped pinned CLI path/JSON
diagnostic tests pass. Patch reproduction/digests and unchanged runtime verified.
See [SCALAR_VALIDATOR.md](../research/SCALAR_VALIDATOR.md) for exact scope/commands.

Important: source validation happens before typecheck transformations and again
on checked specializations before optimization. Post-codegen counts/state must
be zero/admitted. Profile marker is validation-only: emitted C still needs the
**desktop runtime**. No runtime source or embedded runtime text was modified.
Opt-in detection respects -- and option operands; imports/sidecars are blocked
before loading. Outputs are individually staged, not a two-file transaction;
builds must honor failure status and serialize writers.

Exact next steps:
1. Read SCALAR_PROFILE.md runtime lifecycle contract and RUNTIME_STARTUP.md.
2. Prepare a fresh patched tree, then add a separate tracked runtime adaptation:
   inline gs_rt_init/gs_stack_block and generated goose_exit need explicit
   zero-region paths. Replacing only external gs_rt_start leaves calloc/free.
3. Provide a minimal non-returning panic boundary preserving initialization
   guards and checked arithmetic. No heap formatting/signals/threads/longjmp.
4. Verify lifecycle/restart/invalid transitions, zero selected heap/VM/signal/
   pthread calls, and final symbols at -O0/-O2; run desktop regressions.
5. Only after those gates, pin/install official ESP-IDF and build its baseline
   before the generated leaf component. No hardware action without authorization.

Commands:
```sh
git status --short --branch
git log -3 --oneline
python3 tools/test_scalar_validator.py --compiler build/goose-scalar/goose
# If absent, follow tools/README.md; preparation refuses an existing destination.
```

Blockers: runtime/target ABI/alignment/stack budget still unverified; no SDK
release or board selected; full upstream suite not run; known upstream warnings;
license/distribution inventory pending. Grapify unavailable in prior check.
Recommend Astra/high for next runtime safety work. [Architecture](ARCHITECTURE.md),
[decisions](DECISIONS.md), [roadmap](ROADMAP.md), [learning notes](LEARNING_NOTES.md).

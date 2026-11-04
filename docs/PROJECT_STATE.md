# Project state

Updated 2026-11-05 (runtime work began 2026-11-04). Reconcile with Git/source.
Current evidence: research/SCALAR_RUNTIME.md, scalar-runtime-results.json,
patches/goose/{0002-scalar-v0-runtime.patch,runtime-manifest.json}, and runtime
and validator test tools. Earlier M1 and validator evidence remains in research/.

## Current milestone and task

M1 complete as feasibility analysis. M2a in progress: **scalar-v0 validator and
isolated runtime ABI 1 pass host gates**. Current task complete: zero-region
lifecycle, versioned panic boundary, dependency/observer/arithmetic/regression
verification and reproducible patch preparation. No actual Xtensa build yet.
Next: pin/install the official ESP-IDF/toolchain and build its unchanged baseline.

## Completed

- Agent recovery/skill, roadmap, architecture, decisions, learning notes and Git
  checkpoints established. Grapify unavailable in prior installed-root/tool
  checks; standard source tools used, no invented Grapify command.
- Official reference pin 335fddc13dc74666398ffe160ec8a8f2958329d0 remains clean
  in .cache/goose. Tracked patch 0001 and manifest remain unchanged.
- Patch 0002 selects canonical runtime_scalar.h, bypasses desktop init/stack
  block/teardown, and emits zero-region assertions plus cold/ready transitions.
  Only argc=0/argv=NULL is supported, including repeated init calls.
- Same widened checked i32 add/sub/mul/neg rules; lifecycle/overflow/unreachable
  errors call required non-returning ge_scalar_v0_panic_v1. ABI marker 1 and
  reserved export prefix prevent accidental hook collisions; no fallback stub.
- Runtime text regenerated with upstream generator; final regeneration is
  byte-idempotent. Desktop runtime sections/hash/output are unchanged.
- Two-stage preparation checks patch dependency and all final file digests;
  --validator-only mode retains/retests the historical first stage.
- Native and generic i386 freestanding generated objects for two libraries at
  -O0/-O2 have exactly the panic hook unresolved, without LTO/section GC.
- Selected heap/VM/signal/pthread lifecycle counters are zero; cold/ready,
  idempotence/restart, invalid calls and arithmetic failure paths are verified.
- 496 deterministic arithmetic cases agree with Python values/overflow outcomes.
  Desktop probes and scoped upstream frontend regressions also pass.

## Discoveries and constraints

- Zero regions alone are insufficient; source/type checks and codegen invariants
  remain enforced. GS_MAX_STACKS=0 still disables the ordinary upstream limit.
- Codegen emits checked GS_UNREACHABLE guards at -O0; scalar runtime must handle
  those too. They now forward to the same panic boundary with source location.
- A small isolated section avoids unused desktop helpers even at -O0. The only
  tested generated-object external symbol is ge_scalar_v0_panic_v1.
- The platform owns the non-returning/no-allocation hook contract. Linux test
  binding uses write/_Exit; it is not an ESP-IDF binding. Host libc/startup and
  observer internals are outside the generated-code no-heap/OS claim.
- Scalar runtime has independent ABI version 1; unchanged desktop sections retain
  hash d22ae129d92b and byte-identical emitted runtime C. Existing canonical
  desktop runtime files remain byte-identical to the source pin.
- Generic i386 compile evidence is not Xtensa execution or aggregate/reference
  portability. Native task stack, target memory placement and footprint unknown.

## Incomplete / blockers

- No ESP-IDF release/toolchain pinned or installed for this project; no unchanged
  baseline target build or generated Goose component built/linked for ESP32-S3.
- ESP-IDF panic adapter, target ABI/alignment/ELF/map/assembly/stack review.
- Board/serial details and explicit hardware authorization; no flashing occurred.
- No simulator/physical result, interrupts, concurrency, HAL or peripherals.
- Full upstream compiler/LSP/sanitizer suites not run; scoped regressions only.
- Existing upstream Release warnings remain documented (unused items and GCC
  Roots/small_vector maybe-uninitialized); no new runtime compile warning needed
  suppression to pass the tests.
- Overall project license/distribution inventory pending; Goose Apache-2.0 text,
  adapted-code provenance and modified-file notices retained with patches.

## Files changed this task

New: patches/goose/{0002-scalar-v0-runtime.patch,runtime-manifest.json},
tools/test_scalar_runtime.py, tests/scalar_v0/{panic_host.c,lifecycle_host.c,
arithmetic_host.c,arithmetic.goose}, research/{SCALAR_RUNTIME.md,
scalar-runtime-results.json}.
Updated: preparation/validator tools, test host message, tools/patch READMEs,
src/README.md, project README, architecture/profile/roadmap/decisions/learning,
state and handoff, reference inventory. Ignored sources/builds are disposable;
tracked patch chain/manifests are the durable implementation.

## Verification

- Bootstrap Release build, upstream runtime regeneration and final rebuild: PASS.
- `python3 tools/test_scalar_runtime.py --compiler build/goose-scalar-runtime/goose`:
  PASS, 560 commands (179 expected failures), including 496 arithmetic cases.
- Current validator suite: PASS, 235 commands (209 expected failures), plus nested
  original 19-command desktop host probe. Historical --validator-only workflow:
  PASS, 237 commands on build/goose-scalar/goose. Logs restored to current mode.
- `python3 tools/runtime_probe.py --compiler build/goose-scalar-runtime/goose`:
  PASS, 32 normal desktop runtime commands (six expected failures).
- Scoped upstream CLI-path and JSON diagnostic suites: PASS. Desktop emitted
  runtime C byte equality, canonical desktop files and hash: PASS.
- Fresh patch-chain/file digest reproduction and generator idempotence: PASS.
- Strict C host syntax, Python syntax, local doc links and Git whitespace checks
  recorded at final checkpoint; source/runtime behavior changes tested above.
- Initial missing GS_UNREACHABLE and second-patch new-file metadata were corrected
  with new hypotheses before final successful runs; see SCALAR_RUNTIME.md.
- Xtensa build / simulator / hardware / SDK panic adapter: NOT RUN / not implemented.

## Git and next action

Branch main; no remote. Previous verified implementation: 6250b4a (validator).
The runtime checkpoint is the commit containing this file; resolve exact hash
with `git rev-parse HEAD` after commit. Clean on recovery; all task changes are
intended to be committed, then git status verified. Reference checkout stays clean.
Development source .cache/goose-scalar-runtime, binary build/goose-scalar-runtime/goose;
rebuild from patches if absent. Compiler reports 335fddc+scalar-v0-runtime,
desktop runtime d22ae129d92b. No source edit is durable unless in the patches.

Next: inspect installed SDK tools, browse official current release/toolchain
requirements, pin an ESP-IDF commit and tools in a project-local reproducible
setup, then build the unchanged official ESP32-S3 baseline. Only afterward add
a narrow app_main/panic adapter for the generated leaf library and inspect target
symbols/maps/assembly. Do not flash or start HAL work yet.
Recommend Sol/medium for routine SDK setup; Astra/high for target ABI/toolchain
blockers. No model switch, paid API or hardware operation was initiated.

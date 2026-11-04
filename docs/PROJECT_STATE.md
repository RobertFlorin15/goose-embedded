# Project state

Updated 2026-11-04. Reconcile with Git and source on recovery.
Authoritative current task evidence: research/SCALAR_VALIDATOR.md,
scalar-validator-results.json, patches/goose/{0001-scalar-v0-validator.patch,manifest.json},
and tools/test_scalar_validator.py. Earlier M1/runtime investigations remain
in research/FEASIBILITY.md, EXPERIMENTS.md and RUNTIME_STARTUP.md.

## Current milestone and task

M1 complete as source-backed feasibility analysis. M2a in progress:
**opt-in scalar-v0 compiler validator implemented and host-tested**.
Current task complete: tracked patch, reproducible preparation, rejection and
desktop regression tests. Runtime startup has NOT been adapted.
Next task: restricted zero-region lifecycle and platform panic boundary.

## Completed

- Persistent agent instructions/skill, roadmap, architecture, decisions,
  educational notes and Git checkpoints established.
- Clean official Goose pin 335fddc13dc74666398ffe160ec8a8f2958329d0 retained in
  .cache/goose. Development patched copy .cache/goose-scalar, compiler binary
  build/goose-scalar/goose. No upstream runtime files changed.
- Explicit --embedded-profile=scalar-v0 CLI mode: C library emission only;
  forced GS_DEBUG=1; parsed source allowlist/call-cycle checks before typecheck;
  checked-specialization validation before optimization; zero-region and
  unsupported-codegen-state invariants before output publication.
- Early import/namespace/extern directive and sidecar rejection; conflicting
  options blocked before early actions. Normal arguments after -- and option
  operands do not accidentally enable the profile.
- Staged output writes; alias/staging/output-failure tests and source diagnostics.
- Tracked patch/license/notices/digests; fresh pinned archive + verified patch
  preparation refuses wrong pin or existing destination and reproduces source.
- 46 source rejection fixtures and malformed sidecar checked at -O0/-O2;
  accepted computation/restart and four arithmetic overflow paths verified.
- Normal desktop probes and scoped upstream CLI/diagnostic suites pass.
- Previous host startup trace, ABI/layout witness and reference/license research
  remain documented. Grapify unavailable in prior installed-root/tool checks;
  no commands invented or new installation attempted.

## Discoveries and constraints

- Zero regions alone do not exclude references, foreign calls or native
  recursion. GS_MAX_STACKS=0 disables the upstream limit.
- Typechecking can fold literal arithmetic before optimization. Validator
  distinguishes admitted constants from actual stored/runtime scalar types.
- Profile C uses GS_SCALAR_V0_VALIDATED=1 as a validation marker, **not** an
  embedded runtime ABI. It still links the existing desktop runtime.
- That runtime allocates metadata, installs signal/alternate-stack facilities,
  queries native stack attributes and locks shutdown bookkeeping, even when the
  application has zero regions/workers. Both inline init and generated exit
  need explicit restricted paths in the next task.
- Pointer layouts and packing remain unverified on Xtensa; no aggregate or
  reference support is claimed. No MCU footprint or task stack budget known.

## Incomplete / blockers

- Allocation-free lifecycle, failure hook and corresponding no-OS/heap evidence.
- Pinned official ESP-IDF/toolchain installation/baseline and actual target build.
- Board/serial details and explicit hardware-operation authorization; no flashing.
- Target ABI/alignment/ELF/map/stack review, simulator or physical execution.
- Interrupts, concurrency, HAL and peripherals are not implemented.
- Full upstream compiler/LSP/sanitizer suites not run; scoped tests only.
- Previously recorded upstream Release warnings remain unresolved.
- Overall project license/distribution inventory remains incomplete; patch
  retains Goose Apache-2.0 license/context and modified-file notices.

## Files changed this task

New: .gitattributes (literal patch context whitespace), patches/goose/{0001-scalar-v0-validator.patch,manifest.json,LICENSE.upstream,README.md},
tools/{prepare_scalar_compiler,test_scalar_validator}.py,
tests/scalar_v0/{accepted.goose,host.c,rejections.json},
research/{SCALAR_VALIDATOR.md,scalar-validator-results.json}.
Updated: README.md, tools/README.md, research/{FEASIBILITY,REFERENCES}.md and
state/handoff/architecture/roadmap/decisions/learning/profile documentation.
Ignored development source/build artifacts are not the durable implementation;
the tracked patch and manifest are authoritative.

## Verification

- Patched Release CMake build: PASS; existing upstream warnings documented.
- `python3 tools/test_scalar_validator.py --compiler build/goose-scalar/goose`:
  PASS, 237 top-level commands: 209 expected exit-1 cases and 28 exit-0 commands.
  Includes -O0/-O2 positive/negative/profile/CLI/output/preparation checks.
- Nested original desktop host probe: PASS, 19 commands on the patched compiler.
- Scoped pinned upstream check_cli_paths(exe, None, base) and
  check_diagnostics_json(exe, base): PASS after final CLI correction.
- Clean archive+patch source reproduction, patch/file digests and runtime byte
  comparison: PASS; no runtime files or runtime_inline.h changed.
- Python syntax, strict C host syntax, documentation links, Git whitespace: PASS.
- Corrected initial LSP signature ambiguity, a draft fixture, preparation Git
  discovery, upstream harness layout and opt-in argument scanning; evidence and
  final tested behavior recorded in research/SCALAR_VALIDATOR.md.
- Restricted runtime/target compilation/simulator/hardware: NOT RUN / pending.

## Git and next action

Branch main; no remote. Prior verified commit fcc2689 (startup/design checkpoint).
This implementation checkpoint is the commit containing this state; use
`git rev-parse HEAD` for its exact hash after commit. Working tree was clean on
recovery; all task changes are intended to be committed, then verify git status.
Original reference checkout remains clean; generated artifacts/caches ignored.

Next: using the tracked patch preparation workflow, add restricted lifecycle
branches so admitted zero-region code avoids inline calloc, desktop gs_rt_start,
thread/signal setup and generated free. Preserve cold/ready/idempotence/restart
and checked arithmetic through a non-returning platform panic boundary. Test
selected calls and final symbols at -O0/-O2 before any ESP-IDF integration.
Recommend Astra/high for this runtime safety/ABI work; Sol/medium for routine
SDK setup afterward. No automatic model switch, paid API or hardware operation.

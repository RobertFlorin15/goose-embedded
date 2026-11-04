# Project state

Updated 2026-11-04. Read this against Git status/history and actual artifacts.
Evidence: research/FEASIBILITY.md, EXPERIMENTS.md, RUNTIME_STARTUP.md,
{host,runtime}-results.json, runtime-summary.json and upstream.json.

## Current milestone and task

M1 complete as source-backed feasibility analysis; target execution remains
conditional. M2a in progress: startup/symbol inventory and scalar-v0 design
complete. No target profile or runtime adaptation has been implemented.
Current task: checkpoint the verified startup investigation and profile design.
Next task: implement a tracked, opt-in compiler validation patch for scalar-v0.

## Completed

- Established agent recovery instructions/skill, roadmap, architecture, decision
  log, educational notes, state/handoff, Git main and M1 foundation commits.
- Pinned official Goose 335fddc13dc74666398ffe160ec8a8f2958329d0; clean ignored
  copy .cache/goose, existing Release compiler /tmp/goose-build/goose, runtime
  d22ae129d92b. Source revision/cleanliness rechecked this session.
- M1 host probes: scalar/growth C emission and execution, C-export lifecycle/
  restart, zero-region scalar leaf and freestanding 32-bit layout witness.
- New separate-runtime probe: per-object/final symbol inventories, observed
  startup/exit calls, idempotence/restart/export results, pre-init/post-exit and
  checked-overflow failures at Goose/native -O0 and -O2.
- New upstream counterexamples: foreign call, marked recursion and reference
  export all report zero regions; growth accepts GS_MAX_STACKS=0 with two.
- Specified compiler structural/type allowlist, count invariants, restricted
  lifecycle/failure boundary and acceptance tests in docs/SCALAR_PROFILE.md.
- Grapify unavailable in previously inspected installed roots/tool catalog;
  no new installation or tool access; standard source inspection used.

## Verified discoveries

- C++20 host compiler -> typed/specialized AST -> optimization/BCE -> C.
- VM runtime, C heap metadata and hard-coded 64-bit reference layouts remain
  target obstacles; actual Xtensa failure/miscompilation is not yet reproduced.
- Zero-region leaf startup still does two direct calloc calls, one malloc,
  signal setup, page-size and native-thread stack queries on this Linux host.
- Separate emitted runtime is built with GS_NEED_THREADS=1 even for no-worker
  applications; observed shutdown takes a pthread mutex and performs frees.
- No selected VM mapping calls occurred during zero-region lifecycle; unused
  VM symbols can still appear in objects/final link. See observer limitations.
- GS_MAX_STACKS=0 disables count enforcement; count alone cannot exclude foreign
  calls, reference ABI or native recursion. Profile rejection is NOT implemented.

## Incomplete / blockers

- Compiler allowlist/option and restricted runtime need tracked patches/tests.
- No ESP-IDF/toolchain release pinned or installed for this project; no target
  C build, ELF/assembly/map review, simulator or physical hardware verification.
- idf.py and xtensa-esp32s3-elf-gcc previously absent from PATH; no board/serial
  details or authorized hardware operation. No flashing occurred.
- 32-bit aggregate/reference layouts, packed alignment, native task stack budget,
  concurrency and interrupts remain unsupported/unverified.
- Upstream Release warnings remain documented; full upstream suite not run.
- Project license/distribution inventory incomplete; not ready for public release.

## Files modified this task

New: docs/SCALAR_PROFILE.md, research/RUNTIME_STARTUP.md,
research/runtime-{results,summary}.json, tools/runtime_probe.py,
tests/runtime_{observer.c,observer.h,lifecycle_host.c},
tests/profile_candidates/{foreign,recursive,reference}.goose.
Updated: README.md, tools/README.md, research/FEASIBILITY.md,
docs/{ARCHITECTURE,DECISIONS,LEARNING_NOTES,ROADMAP,PROJECT_STATE,HANDOFF}.md.
No upstream source or original host probe changed; generated artifacts ignored.

## Verification

- Existing M1 evidence: Release build and 19-command host probe passed in prior
  task, with upstream warnings. Not rerun: no relevant baseline code changed.
- `python3 tools/runtime_probe.py --compiler /tmp/goose-build/goose`: PASS,
  32 commands; six deliberate exit-1 failures matched expected diagnostics;
  all other commands exit 0. Traces at both levels include two restart cycles.
- Both new C observer/host sources pass -std=c11 -Wall -Wextra -Werror
  -fsyntax-only; Python AST parse and archived-log consistency checks pass.
- Local Markdown links resolve; Git whitespace check passes before checkpoint.
- Initial probe stream assertion and recursion fixture syntax errors corrected;
  root causes recorded in research/RUNTIME_STARTUP.md.
- Scalar-v0 rejection/target build/simulator/hardware: NOT RUN, not implemented.

## Git and next action

Branch main; no remote. Previous verified checkpoint: 757a6d8 (M1 handoff);
verified M1 implementation: a5d7f672a90a73ce92c30d2eb9d6f45af180dc1c.
This task's design/probe checkpoint is the commit containing this state update;
resolve its exact hash with `git rev-parse HEAD` after commit. Working tree was
clean on recovery; all listed task changes are intended to be committed.
Check actual dirty state when resuming; .cache/ and build/ remain ignored.

Next: add tracked Goose patch/build instructions for explicit scalar-v0 option
and pre-optimization source/type validation. Cover unsupported and unused/dead
constructs with negative tests at -O0/-O2; preserve desktop behavior. Then add
the restricted lifecycle/runtime in a separate verified change. Use
SCALAR_PROFILE.md as the acceptance contract, not a claim of current support.
Recommend Astra/high for compiler validation/runtime safety design; Sol/medium
for routine setup after the safety gates. No automatic model switch or paid API.

# Project state

Updated 2026-11-05. Reconcile with Git/source. Current evidence:
[FATAL_CASES.md](../research/FATAL_CASES.md),
[fatal-case-results.json](../research/fatal-case-results.json).
Previous normal/config/stack/compiler reports remain valid historical evidence.

## Current milestone and task

M1 analysis and M2a scalar leaf cross-build/ABI gate complete. Current task:
**selectable success/cold-export/overflow firmware and separate fatal saved-log
checks verified by target compilation, host execution and synthetic captures**.
M2b physical execution remains unverified. No physical/simulator execution,
device capture, observed halt, actual watermark samples or full task stack bound.
HAL remains blocked. Next: audit fatal SDK/exception stack requirements and record
remaining unbounded paths before any authorized per-board execution planning.

## Completed tasks

- Durable instructions/skill, roadmap, architecture/decisions/learning and handoff
  established. Grapify unavailable in prior checks; standard source tools used.
- Goose 335fddc13dc74666398ffe160ec8a8f2958329d0 with tracked scalar validator/runtime
  patches 0001/0002 unchanged. Versioned SDK panic binding unchanged.
- SDK v6.0.2/7101770dc6db2667b3c477cc31365dd1acd6db4e, 25 recursive submodules,
  Xtensa GCC 15.2.0 (esp-15.2.0_20251204), tools and Python lock remain pinned.
- Existing acyclic scalar profile, lifecycle checks, target ABI witness and
  dependency/assembly checks remain enabled. No desktop-runtime or Goose API change.
- Ordered defaults overlays, explicit config labels, byte snapshots/target siblings,
  mutation/unknown-symbol/effective policy checks and per-level manifests preserved.
- Normal app retains full SDK descriptor ELF identity, four watermark samples and
  completion marker. The default case remains success with the same serial format.
- CMake/CLI select separately compiled success, cold-export or overflow. Fatal
  apps print identity/case, take only before sample (completed=1), invoke deliberate
  invalid operation, and use a distinct fallback panic if it unexpectedly returns.
- Manifests now identify case. Missing legacy case means success only; fatal
  manifests/captures must explicitly agree. Probe checks actual case definitions.
- Shared capture loader preserves artifact/config/hash/path/JSON/input checks.
  Normal checker rejects fatal builds. Separate fatal checker requires selected
  identity/case, exact details and terminal SDK halt cue; rejects conflicting,
  duplicate, missing, reordered, reset, normal and known unrelated fault output.
- Protocol documented in docs/FATAL_RUN_LOG_FORMAT.md; ADR012 records tradeoffs.
  Multiple future boards remain separate configurations; no guessed board presets.

## Technical findings and limits

Verified source: pinned SDK esp_system_abort forwards to panic_abort; panic.c
prints supplied details verbatim with reason/description cleared and later prints
CPU halted under PRINT_HALT. It prints the cue before the final halt routine.
Thus matching saved text proves neither physical execution nor persistent halt.
All offline results keep hardware_execution_proven and stack_bound_proven false;
fatal results also keep halt_proven false. Evidence type is a declaration only.

Host fatal tests use actual app/generated runtime/real bridge with SDK doubles,
checking message, pointer record, file/line and partial sample state. They do not
execute SDK panic machinery. Cold export has NULL/zero source record; overflow
has static source file and positive line. Unknown diagnostic text still requires
human review; parsers cannot detect every fault or events after capture ends.

Normal app frame remains 48 bytes; fatal frames O0/O2 are 48/32. These are compiler
frames, not whole-task bounds. ROM callbacks, exception/window/interrupt overhead
and complete stack analysis remain open. Control defaults 2 MB flash/3584 stack
are build fixtures, not proof of module compatibility or sufficient memory.
Identity output affects lifetime readings; completion/return/deletion lie outside
normal samples. Fatal sample record is partial and rejected as normal debugger data.

## Verification

- `python3 -m unittest discover -s tests -p 'test_scalar*.py' -v`: PASS, 41 cases
  (29 normal/config/integrity, 12 fatal plus table subcases), log in
  build/fatal-fixtures/unit-tests.log. No SDK/hardware needed for these unit tests.
- Three probes: build/esp-idf-fatal-{cold,overflow,success}, each PASS, 83 commands,
  including 22 expected nonzero exits; six target O0/O2 firmware builds. Existing
  ABI/policy/dependency/arithmetic/normal-sequencing/unit checks pass alongside
  actual fatal app/runtime/bridge host checks. Image descriptor matches full ELF.
- 27 supplementary checks: six synthetic CLI captures consistent; six opposite
  validator rejects; one cross-case manifest reject; twelve host wrong-case rejects;
  CMake and preprocessor unknown-case rejects. All six compile databases match
  selected case. Permanent definition guard added after full probes; equivalent
  checks independently verified against all six existing compile databases.
- App bytes O0/O2: success 146144/145824, cold-export 145808/145520,
  overflow 145872/145600. SDK/Goose reference trees clean; adapted compiler source
  digests remain pinned. Generated warnings unchanged; no suppression introduced.
- One supplementary harness assertion failed due to an incorrect generated-header
  path. Corrected include directory; intended unknown-case rejection then passed.
  No target/runtime failure. Full compiler suites not rerun (implementation unchanged).
- Python syntax, evidence hashes/artifacts/config/source and Git whitespace checked.
  Physical/simulator/flash/serial/debug: NOT RUN.

## Incomplete / blockers

- Physical normal/fatal behavior, observed halt, actual watermark values and full
  SDK/ROM/exception/window stack requirements remain unverified. M2b blocks HAL.
- No exact board/module/flash/PSRAM/console inventory or hardware authorization.
  User has several variants; review each concrete configuration before operations.
- Full upstream compiler/LSP/sanitizer suites, license/distribution inventory and
  project license pending. No SDK/tool/generated binary redistribution.

## Files and Git

New: fatal validator, fatal host fixture, fatal unittest file, fatal protocol,
research/FATAL_CASES.md and fatal-case-results.json. Updated: example CMake/main,
probe/config/normal loader, normal tests, root/tools docs, roadmap/architecture/
decision/learning and state/handoff. Compiler/runtime patches and panic adapter unchanged.

Branch main; no remote. Prior completed checkpoint:
336443af4f721e511367ccad9fb9c35296d6ddd6. Current verified checkpoint is the commit
containing this file (`git rev-parse HEAD`); verify status. Task changes intended
to be committed together. Unrelated untracked .vscode/ preserved and excluded.
Raw evidence ignored under build/esp-idf-fatal-* and build/fatal-fixtures; summary
tracked. Fresh outputs required for full probe reruns.

## Next action / model

Audit source/assembly of fatal SDK entry/exception paths and list stack-budget
unknowns, separating compiler frames from whole-task bounds. Astra/high recommended
for exception/window/ROM stack reasoning; Sol/medium for routine tool maintenance.
Checkpoint before switching; no in-session model switch assumed. Keep per-board
hardware authorization and M2b/HAL gates. No paid API or orchestration work.

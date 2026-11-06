# Project state

Updated 2026-11-06. Reconcile with Git/source. Current evidence:
[FATAL_STACK_AUDIT.md](../research/FATAL_STACK_AUDIT.md),
[fatal-stack-results.json](../research/fatal-stack-results.json).
Earlier fatal/config/normal/compiler reports retain their historical evidence.

## Current milestone and task

M1 analysis and M2a scalar leaf cross-build/ABI gate complete. Latest technical result:
**fatal SDK/exception stack ownership and individual-frame audit complete as
static analysis, with remaining budget requirements explicitly unresolved**.
M2b physical execution is unverified and HAL blocked. No physical/simulator
execution, actual stack sample, observed halt or complete stack bound exists.
Next independent task: inventory pinned compiler/SDK/tool licenses and potential
distribution obligations before selecting a project license.

## First GitHub push preparation (2026-11-06)

Completed .gitignore for downloaded/build output, Python environments/caches,
local editors/OS files, dotenv/private-key containers, CMake/native products and
application-local ESP-IDF config/downloads. Keep defaults, lockfiles, test stubs,
agent memory, patches and reviewed JSON/log evidence eligible. Existing .vscode/
content preserved and now ignored. Verification:24 excluded paths +17 eligible
paths pass git check-ignore --no-index; no tracked files match ignore rules;
git diff --check passes. No firmware or code change, so no compiler/build rerun.

Reconciled actual Git configuration: origin is
https://github.com/RobertFlorin15/goose-embedded.git; prior "no remote" statement
was stale. No main upstream tracking branch configured at inspection. This task
does not push or establish remote contents. After this checkpoint, user can run
`git push -u origin main`. Project license inventory remains the next engineering
task; first push is not a licensed release or hardware milestone.

## Completed tasks

- Durable instructions/skill, roadmap, architecture/decisions/learning and handoff
  established. Grapify unavailable in prior discovery; standard tools used.
- Goose 335fddc13dc74666398ffe160ec8a8f2958329d0 plus scalar patches 0001/0002;
  SDK 7101770dc6db2667b3c477cc31365dd1acd6db4e/v6.0.2; 25 recursive submodules;
  GCC 15.2.0/esp-15.2.0_20251204; SDK tools/Python lock remain pinned.
- Restricted scalar validator/runtime, ABI witness and SDK panic bridge already
  compile for target and execute in host tests. No changes to them this task.
- Explicit defaults/config snapshots and effective policy checks, per-case/level
  manifests, normal and fatal protocols/checkers remain in place. Default success,
  cold-export and overflow have six prior passing target builds O0/O2.
- New tools/audit_scalar_fatal.py verifies passing fatal probe, SDK/source/artifact
  identity and retains four linked disassemblies/140 individual-symbol records.
  Reviewed pre-trap paths are manual source/assembly analysis; no automatic graph
  closure or whole-task cost claim. Missing assembly frame remains null, not zero.
- New extractor tests protect unknown frames, symbol boundaries, missing symbols,
  direct/indirect calls and multiple-entry refusal. Fatal validator now rejects
  SDK |<-CORRUPTED; |<-CONTINUES remains allowed without claiming full backtrace.

## Verified discoveries / assumptions

- Ordinary task fatal exception stays on task stack. Linked prologue allocates 192
  bytes and writes pseudo-save data at new a1-16 (store address 208 below trapped
  a1). Allocation size is not deepest touched address; ABI save-area overlaps and
  window spills still need peak analysis. Configured 1536-byte ISR stack is separate.
- Visible pre-trap frame sums including SDK parents: cold 336/O0, overflow 464/O0,
  both 240/O2. No inclusive exception/console/ROM or whole-task bound. Init, prints
  and sampling return before the trap; their lifetime peaks are separate concerns.
- SDK panic_handler frame 80, esp_panic_handler 32; cache preparation frame 32 returns
  before main panic processing. Source callbacks retain backtrace on Xtensa abort;
  iterative depth limit 100 is not 100 nested C frames. No target SDK panic executed.
- SDK panic printing uses its UART and secondary USB routines, distinct from normal
  ROM printf. Output branches are sequential; ROM delay/reset services and indirect
  calls remain open. Current control config enables UART + secondary USB Serial/JTAG.
  Tool deliberately rejects other console selections for separate review.
- Halt cue precedes watchdog shutdown, module-reset/ROM UART drain and final loop.
  Matching text proves neither final nor persistent physical halt. All offline
  proof flags remain false. Runtime exception-table integrity is an assumption;
  SDK default dispatch is source-backed, not attested from a running device.
- Scope stays one serial normal-task Goose caller with caches available. No
  ISR/concurrency/HAL. Multiple boards require separate reviewed configs; generic
  control 2 MB/3584 stack is neither a board preset nor stack-sufficiency evidence.

## Verification

- `python3 -m unittest discover -s tests -p 'test_scalar*.py' -v`: PASS, 47 cases
  (29 normal/config/integrity, 13 fatal, 5 audit extraction) plus table subcases.
  Log build/fatal-audit-unit-tests.log. No SDK/hardware required for unit tests.
- Read-only audit: PASS four fatal ELFs, 140 symbol records; SDK/probe/source/
  manifest/artifact identity checks. Output build/fatal-stack-audit-final. Compiler
  frames recorded individually; no default zero for hand-written assembly.
- Four refusal checks pass: normal build, existing output, input-tree overlap and
  tampered ELF. Failed audit stays failed. Six existing synthetic captures still
  validate with current normal/fatal tools. No new target compilation needed;
  compiler/runtime/application/SDK/panic binding unchanged.
- Historical checkpoint 4352678: six target builds, 83 commands/22 expected nonzero
  exits each configuration, 41 unit cases and 27 supplemental checks. Historical
  validator/test hashes describe that prior version; current hashes in new summary.
- Python syntax, evidence/artifact hashes, local documentation links and Git
  whitespace checked. SDK and Goose reference trees clean. Adapted source digests
  remain pinned. No new build/runtime failure; physical/serial/debug/flash NOT RUN.

## Incomplete / blockers

- Full lifetime and fatal SDK/ROM/interrupt/window/exception stack budgets remain
  open; exact missing evidence listed in audit report. No arbitrary safety margin,
  stack increase or speculative emergency-stack runtime introduced.
- No physical normal/fatal output, persistent halt or real watermark evidence.
  Exact module/flash/PSRAM/console inventory and explicit authorization required
  before any concrete hardware operation. User has multiple unspecified boards.
- Dependency/distribution inventory and project license pending. Full upstream
  compiler/LSP/sanitizer suites remain pending; implementations unchanged this task.
  No SDK/tool/generated binary redistribution.

## Files and Git

This checkpoint changes .gitignore and the state/handoff only. The following
implementation files describe the prior technical checkpoint.

New audit tool/unit tests/report/JSON summary; updated fatal validator/rejection
test, protocol, README/tools docs, architecture/roadmap/learning and state/handoff.
No target/compiler/runtime/panic adapter source modifications.
Branch main; origin configured as above. Prior verified technical checkpoint:
b100cc1 (resolve full hash with git rev-parse b100cc1).
Current checkpoint is the commit containing this file (`git rev-parse HEAD`);
verify status. Related changes intended to be committed together. Unrelated
local .vscode/ preserved/ignored. Raw audit/test artifacts ignored under build/.

## Next action / model

Inventory exact license files/notices for pinned Goose and its compiler
third parties, ESP-IDF/submodules and installed tool packages. Distinguish local
use, linking/generated output and redistribution; record unknown obligations and
required follow-up without guessing compatibility or selecting a license yet.
Sol/medium for the bounded inventory. Astra/high remains recommended for complete
window/exception/ROM stack reasoning. No model switching assumed; no paid API,
hardware or HAL action authorized by this checkpoint.

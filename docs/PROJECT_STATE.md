# Project state

Updated 2026-11-06. Reconcile with Git/source. Current evidence:
[LICENSE_INVENTORY.md](../research/LICENSE_INVENTORY.md),
[FATAL_STACK_AUDIT.md](../research/FATAL_STACK_AUDIT.md),
[fatal-stack-results.json](../research/fatal-stack-results.json).
Earlier fatal/config/normal/compiler reports retain their historical evidence.

## Current milestone and task

M1 analysis and M2a scalar leaf cross-build/ABI gate complete. Latest result:
**pinned license evidence inventory collected (static, no legal clearance)**.
Prior technical result: fatal SDK/exception stack ownership and individual-frame
audit (static; budget requirements explicitly unresolved).
M2b physical execution is unverified and HAL blocked. No physical/simulator
execution, actual stack sample, observed halt or complete stack bound exists.
Next: resolve the exact firmware link set (fresh scalar build retaining map/
project description) and let the user choose a project license.

## License inventory (2026-11-06)

New tools/license_inventory.py (offline, read-only) + tests/test_license_inventory.py
(8 cases). Report research/LICENSE_INVENTORY.md; reviewed JSON
research/license-inventory-results.json (sha256 156071f3...209d). Inputs fetched
this session into ignored .cache/: Goose clean at pin; ESP-IDF partial clone
.cache/esp-idf-v6.0.2-meta at 7101770 (tag object b0d7ee87 matches) with 25
submodules matching recorded scalar evidence; pinned Xtensa archive (sha256
matches pin) in .cache/dist, license dir also extracted to .cache/toolchain-licenses.
No SDK tools installed, no build, no hardware.

Findings: Goose Apache-2.0, no NOTICE; compiler statically links LGPL-2.1
TinyCC (RELICENSING partial with NO/? entries); libtcc1.c GPL-2.0+ with linking
exception; subprocess.h Unlicense; cute_spirv zlib OR Unlicense, ckit public
domain (latter two previously unlisted). ESP-IDF root Apache-2.0; FreeRTOS/
Xtensa MIT, TLSF BSD-3 (no root license file), mbedtls Apache-2.0 OR GPL-2.0+,
lwIP/OpenThread/protobuf-c/micro-ecc BSD-style. esp_libc Kconfig defaults to
picolibc with GCC; project defaults do not override. Toolchain: libgcc GPL-3 +
Runtime Library Exception text; picolibc per-file manifest, copyleft stanzas
name only test/script files. Python lock licenses not inspected.

Verification: 8 new + 47 existing unit tests pass; inventory run PASS; refusal
checks (non-pinned archive, dirty Goose) exit 1 without output. Raw output
build/license-inventory. Unresolved items listed in the report.

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
- License evidence inventory done; exact firmware link set, effective libc and
  project license selection remain open (see LICENSE_INVENTORY.md). Full upstream
  compiler/LSP/sanitizer suites remain pending; implementations unchanged this task.
  No SDK/tool/generated binary redistribution.

## Files and Git

This checkpoint adds tools/license_inventory.py, tests/test_license_inventory.py,
research/LICENSE_INVENTORY.md and license-inventory-results.json, and updates
README, REFERENCES, tools/README, state and handoff. No compiler/runtime/target/
panic adapter source changes. Branch main; origin
https://github.com/RobertFlorin15/goose-embedded.git. Prior explicit checkpoints:
9713a8b (gitignore), b100cc1 (fatal audit). Current checkpoint is the commit
containing this file (`git rev-parse HEAD`); verify status. .cache/ and build/
remain ignored.

## Next action / model

1. User decision: choose a project license (inventory informs, does not decide).
2. Engineering: with the full SDK setup (tools/README.md), run a fresh scalar
   build and retain the linker map/project_description.json and effective
   sdkconfig to list the actual linked components/libc for firmware notices.
Sol/medium suffices for both. Astra/high remains recommended for complete
window/exception/ROM stack reasoning. No model switching assumed; no paid API,
hardware or HAL action authorized.

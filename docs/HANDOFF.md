# Handoff

2026-11-05. **Selectable fatal firmware and offline checks verified by cross-build,
host execution and synthetic captures only. No physical/simulator execution or
observed halt; M2b and HAL remain blocked.**

Recover AGENTS.md -> PROJECT_STATE.md -> project skill -> Git/source/evidence.
Branch main; no remote. Prior completed checkpoint 336443af4f721e511367ccad9fb9c35296d6ddd6.
Current checkpoint is the commit containing this file (`git rev-parse HEAD`).
Task changes committed together; verify status. Unrelated untracked .vscode/ is
preserved/excluded. Compiler/runtime patches, SDK panic adapter and pins unchanged.

New: `--case success|cold-export|overflow` (default success), mapped to fixed main
compile definitions. Fatal apps print identity and case, keep only before sample
(completed=1), invoke actual invalid operation and never print normal completion.
Returning failure uses a distinct rejected panic. Target case flags checked.
Per-level manifests include case; missing legacy case means success only.
Fatal manifests/captures require explicit matching case.

Offline tools/validate_scalar_fatal.py shares integrity loading with normal tool,
requires exact selected details followed by terminal CPU halted cue, and rejects
wrong case/identity, normal protocol, duplicates/truncation/reordering/resets and
known unrelated faults. Normal tool rejects fatal builds. Results only mean file
consistency; hardware_execution_proven, halt_proven and stack_bound_proven false.
All automated captures declare synthetic. SDK prints halt cue before final halt
routine, so text cannot prove persistent halt. No actual SDK panic executed.

Verified:
- 41 unit tests: 29 normal/config/integrity + 12 fatal, plus table subcases.
- Three full probes, 83 commands/22 expected nonzero exits each: six target builds
  O0/O2, previous ABI/dependency/policy/arithmetic/normal app checks and new actual
  fatal app + generated runtime + real bridge host tests with SDK doubles.
- 27 supplementary checks: six synthetic capture accepts, six opposite-validator
  rejects, cross-case mismatch reject, 12 wrong-case host marker rejects, unknown
  CMake/preprocessor case rejects. All six compile databases match selected case.
  Permanent definition guard added after full builds; equivalent check run separately.
- Full ELF digest in every image matches ELF. App bytes O0/O2: success 146144/145824,
  cold 145808/145520, overflow 145872/145600. app_main frames 48/48 normal, 48/32 fatal;
  no whole-task bound. Control config remains 2 MB/3584 stack (not a board preset).
- One supplementary harness path was wrong; corrected include path and intended
  preprocessor guard then passed. SDK/Goose reference trees clean; adapted source
  digest checks pass. No new warning suppression. No physical operations.

Commands (fresh output for full builds):
```sh
python3 -m unittest discover -s tests -p 'test_scalar*.py' -v
python3 tools/test_esp_idf_scalar.py --case cold-export --output build/new-cold
python3 tools/test_esp_idf_scalar.py --case overflow --output build/new-overflow
python3 tools/test_esp_idf_scalar.py --output build/new-success
python3 tools/validate_scalar_fatal.py --manifest build/new-overflow/O0/run-manifest.json --capture /path/to/capture.json
```
Existing outputs build/esp-idf-fatal-{cold,overflow,success}, build/fatal-fixtures.
Read research/FATAL_CASES.md and fatal-case-results.json for exact evidence and
source/manifest/artifact hashes. docs/FATAL_RUN_LOG_FORMAT.md defines saved files
and SDK source diagnostics; RUN_LOG_FORMAT.md retains normal protocol. Existing
config overlays/IDs continue to work; no new board configurations introduced.

Next exact task: audit source/assembly of fatal SDK/exception entry paths and list
remaining unbounded stack requirements. Use pinned SDK and current app/firmware
assembly; distinguish static compiler frames from task/window/exception/ROM costs.
Do not manufacture a numerical full bound from partial frame sums. Astra/high
recommended for that reasoning; Sol/medium for routine tool maintenance. Checkpoint
before a user model transition; do not assume switching yourself.

User has multiple board types, with no exact inventory/reviewed physical config or
hardware authorization. Do not repeatedly ask for one board as if it defines the
framework. Before concrete flash/serial/debug: review exact module/config and get
explicit authorization. Runtime contract is serial normal task, caches enabled;
no ISR/reentrancy/concurrency/HAL. No actual watermark/serial evidence exists.
License inventory/full upstream suites remain pending. Grapify unavailable in
prior checks; standard inspection used. Setup/pins unchanged in tools/README.md.

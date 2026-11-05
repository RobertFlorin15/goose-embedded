# Handoff

2026-11-05. **Fatal stack ownership/frames audited statically. Whole-task stack,
physical execution and halt remain unverified. M2b and HAL are still blocked.**

Recover AGENTS.md -> PROJECT_STATE.md -> skill -> Git/source/evidence.
Branch main; no remote. Prior checkpoint 4352678ac2b2d580e40eee218c82ef7d42be09a2.
Current checkpoint is the commit containing this file (`git rev-parse HEAD`).
Task changes committed together; verify status. Unrelated untracked .vscode/
preserved/excluded. No compiler/runtime/target app/SDK/panic-adapter changes.

New tools/audit_scalar_fatal.py checks existing passing fatal builds against pinned
SDK, recorded current source, manifests and artifact hashes; retains four full
linked disassemblies and 140 symbol records. Frames without ordinary entry are
null, never zero. It records manual pre-trap paths, direct/indirect indicators and
partial frame sums, not automatic closure or whole-task safety. Current reviewed
console is UART + secondary USB Serial/JTAG; other selections require review.

Findings:
- Cold/overflow pre-trap frame sums O0: 336/464; both O2: 240 including SDK parents.
- Ordinary fatal exception stays on task stack; allocation 192 plus pseudo-save
  stores down to trapped a1-208. Register windows/ABI overlap still unbounded.
  Separate configured 1536-byte ISR stack does not absorb this ordinary fatal path.
- SDK panic_handler 80 and esp_panic_handler 32 are individual frames. Cache helper
  returns before main processing. SDK panic output uses UART/USB character paths,
  not normal ROM formatter. Watchdogs/core coordination/indirect/ROM paths open.
- Backtrace walker is iterative with depth 100; corrupted marker now rejected by
  fatal validator, continuation marker allowed without complete-backtrace claim.
- Halt cue precedes module reset/ROM UART drain/final loop. No physical halt proof.
  Default exception-table dispatch is a source fact, not runtime attestation.

Verified 47 unit tests (29 normal/config, 13 fatal, 5 extraction), four ELF audits,
four refusal checks (normal build/existing output/overlap/tampered ELF), six prior
synthetic captures with current tools. Raw output build/fatal-stack-audit-final,
build/fatal-audit-unit-tests.log, build/fatal-audit-refusals. No target rebuild or
hardware needed. Prior six target builds remain unchanged/historical evidence.
Previous report source hashes refer to its prior compiler/tool checkpoint; current
implementation hashes in research/fatal-stack-results.json.

```sh
python3 -m unittest discover -s tests -p 'test_scalar*.py' -v
python3 tools/audit_scalar_fatal.py --build build/esp-idf-fatal-cold --build build/esp-idf-fatal-overflow --output build/fatal-stack-audit-new
```
Fresh audit output required. Preserve original build artifact layouts; pinned SDK/
local tools required for audit, not for unit tests. Rebuild missing fatal inputs
using tools/test_esp_idf_scalar.py --case cold-export|overflow with separate fresh
outputs (see tools/README.md). No flash/monitor/debug command is involved.
Read research/FATAL_STACK_AUDIT.md and fatal-stack-results.json for evidence,
source permalinks, frame table and exact missing-bound requirements.

Next exact task: inventory license files/notices and distribution considerations
for pinned Goose/compiler third parties, ESP-IDF/submodules and installed tools.
Review research/REFERENCES.md and actual pinned license files first; distinguish
local use, generated/linked output and redistribution. Record unresolved matters;
do not select a project license or assert compatibility prematurely. Sol/medium
for routine inventory; Astra/high for future complete ABI/window/exception/ROM
stack reasoning. Checkpoint before any user model transition.

User has several unspecified board variants; do not repeatedly request one board
as if it defines framework portability. No exact inventory/reviewed physical config
or hardware authorization exists. Before concrete operations: exact module/config
review and explicit authorization. No actual watermark/serial/SDK panic observation,
no complete stack guarantee, no ISR/concurrency/HAL. Grapify unavailable in prior
discovery; standard source/disassembly tools used. Pins/setup unchanged.

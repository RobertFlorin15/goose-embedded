# Handoff

2026-11-06. **Project licensed (root MIT, patches/goose Apache-2.0) and firmware
link set recorded from a fresh target build (static; no legal clearance).
Whole-task stack, physical execution and halt remain unverified. M2b and HAL are
still blocked.**

Recover AGENTS.md -> PROJECT_STATE.md -> skill -> Git/source/evidence.
Branch main tracking origin/main (https://github.com/RobertFlorin15/goose-embedded.git).
Prior explicit checkpoints: 89f5b06 (license inventory), 9713a8b (gitignore),
b100cc1 (fatal audit). Current checkpoint is the commit containing this file
(`git rev-parse HEAD`). Not pushed by the agent.

Latest task: license and link set. Decision 013 records MIT plus the Apache-2.0
patches carve-out; the copyright holder is "Goose Embedded contributors". Open for
the user: confirm the Robert and Krookz13 commit identities are the same person.
New tools/firmware_link_set.py (offline, read-only) counts only objects with bytes
in SHF_ALLOC sections and requires objects plus fill to balance the ELF exactly.
Report research/FIRMWARE_LINK_SET.md, reviewed JSON
research/firmware-link-set-results.json.

```sh
python3 tools/test_esp_idf_scalar.py --output build/esp-idf-scalar-new
python3 tools/firmware_link_set.py --build build/esp-idf-scalar-new --output build/firmware-link-set-new
python3 -m unittest discover -s tests -p 'test_*.py'
```
Results: scalar build PASS (83 commands, build/esp-idf-scalar-license); link set
PASS and repeatable (build/firmware-link-set); 70 unit tests PASS. Findings: picolibc
effective; libgcc zero image bytes; bootloader Apache-2.0 only, no micro-ecc; about
1.2 KB of mbedtls/PSA linked (corrects the inventory); libxt_hal.a license unconfirmed.

Earlier task: license inventory. tools/license_inventory.py (offline,
read-only; refuses wrong/dirty pins, submodule drift, wrong archive hash,
existing output) and tests/test_license_inventory.py (8 cases). Report
research/LICENSE_INVENTORY.md, reviewed JSON research/license-inventory-results.json.
That run used a different fresh clone with a partial SDK. The current machine has
the full .cache/esp-idf-v6.0.2, installed .cache/espressif tools (pinned archive in
.cache/espressif/dist) and build/goose-scalar-runtime; no hardware was used.

Key findings: Goose compiler binary statically includes LGPL-2.1 TinyCC (partial
relicensing only), plus Unlicense subprocess.h and zlib-or-Unlicense cute_spirv.
Firmware side: ESP-IDF Apache-2.0, FreeRTOS/Xtensa MIT, TLSF BSD-3, picolibc
default (Kconfig) with permissive per-file licenses, libgcc GPL-3 + runtime
exception. Generated scalar C embeds Goose-derived Apache-2.0 runtime.

```sh
python3 -m unittest tests/test_license_inventory.py -v
python3 -m unittest discover -s tests -p 'test_scalar*.py' -v
python3 tools/license_inventory.py --sdk .cache/esp-idf-v6.0.2-meta --toolchain-archive .cache/dist/xtensa-esp-elf-15.2.0_20251204-x86_64-linux-gnu.tar.xz --output build/license-inventory-new
```
Results: 8 + 47 tests PASS; inventory PASS (25 submodules, 105 toolchain license
files, 6 NOTICE files unclassified); two refusal checks exit 1 without output.

Still unresolved (see reports): libxt_hal.a license, Python package licenses, and
any configuration other than the control one.

Previous technical checkpoint: tools/audit_scalar_fatal.py checks existing passing fatal builds against pinned
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

Next exact task: (1) the user supplies one board's exact module/flash/PSRAM/console
inventory and explicitly authorizes a run; then follow docs/HARDWARE_VALIDATION.md
for M2b. (2) Offline meanwhile: complete ABI/window/exception/ROM stack reasoning
against research/FATAL_STACK_AUDIT.md's open requirements (Astra/high recommended).

User has several unspecified board variants; no hardware inventory/authorization
exists. No flash/monitor/debug. Grapify unavailable in prior discovery; standard
tools used. Pins/setup unchanged.

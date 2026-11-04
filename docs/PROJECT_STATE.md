# Project state

Updated 2026-11-05. Reconcile with Git/source. Current evidence:
[ESP_IDF_BASELINE.md](../research/ESP_IDF_BASELINE.md),
[esp-idf-baseline-results.json](../research/esp-idf-baseline-results.json).
Earlier compiler/runtime evidence remains in research/SCALAR_{VALIDATOR,RUNTIME}.md.

## Current milestone and task

M1 complete as feasibility analysis. M2a in progress: scalar-v0 validator and
isolated runtime ABI 1 pass host gates; **the unchanged official ESP-IDF
hello_world now builds/links for ESP32-S3**. Current SDK baseline task complete.
Goose-generated code has NOT been built for Xtensa or executed on hardware.
Next: add the scalar leaf component and narrow app_main/panic adapter, then
inspect target ABI/symbols/maps/assembly and native stack assumptions.

## Completed tasks

- Persistent agent instructions/skill, architecture, decisions, roadmap and
  educational notes established. Grapify unavailable in prior installed-root/tool
  checks; standard source tools used. No model router or billed API usage.
- Clean official Goose pin 335fddc13dc74666398ffe160ec8a8f2958329d0 and reproducible
  compiler patch chain/manifests. Opt-in scalar-v0 structural/type/codegen checks
  reject unsupported code before emission; desktop behavior remains default.
- Scalar runtime patch isolates checked i32 helpers, zero-region lifecycle and
  required noreturn ge_scalar_v0_panic_v1, ABI 1. Host/dependency/arithmetic gates
  pass; no desktop runtime sections selected for profile output.
- Official ESP-IDF v6.0.2 at 7101770dc6db2667b3c477cc31365dd1acd6db4e plus all
  25 recursive submodules installed/verified clean in .cache/esp-idf-v6.0.2.
- Official project-local tools installed in .cache/espressif. Pinned tools.json
  selects Xtensa GCC 15.2.0 / esp-15.2.0_20251204. All six downloaded archives
  independently match official hashes. No system installs/profile changes.
- 58 Python packages recorded in tools/esp-idf-python.lock; helper enforces exact
  installed list. Locked official installer replay succeeds in the existing
  environment; package equality remains verified afterward.
- New baseline helper copies unchanged official hello_world, checks source/pins,
  configures esp32s3, builds with two jobs, records logs/versions/artifact hashes,
  checks ELF and SDK cleanliness. No device/flash/serial command exists in it.
- Official baseline linked: ELF32 little-endian Xtensa; app 145424 bytes,
  bootloader 21056, partition table 3072. All six original example files retain
  their hashes. SDK and Goose reference checkouts remain clean.

## Technical discoveries and constraints

- SDK Git pins do not fix Python package versions; upstream constraints refresh
  independently. Package lock and observed constraints hash are retained.
- Host Ubuntu 26.04 x86_64/Python 3.14.4/CMake 4.2.3/Ninja 1.13.2 succeeds for this
  minimal build. flex/bison/ccache absent on PATH; no general prerequisite claim.
- ESP32-S3 example defaults: DIO/2 MB, single-app partition, 100 Hz tick,
  3584-byte main-task stack. These are build settings, not measured board/stack
  properties. Baseline includes ordinary ESP-IDF/FreeRTOS heaps and services;
  no firmware-wide no-allocation claim.
- Source hash/lock/versions support repeatability, not hermetic or byte-identical
  builds. New hosts/package availability/changed official constraints may need
  an explicit reviewed upgrade. Locked replay was not a fresh second install.
- Scalar runtime native/generic i386 objects require only its panic hook at
  -O0/-O2; generic 32-bit evidence is not Xtensa evidence. Platform hook must
  uphold noreturn/no-allocation requirements; current Linux hook is test-only.
- Profile remains single serial normal-task caller only. No ISR, concurrency,
  aggregates/references, arenas, HAL or peripheral support.

## Incomplete tasks / blockers

- Goose leaf target compile/link; ESP-IDF panic adapter, target ABI/alignment,
  ELF/map/assembly and native stack budget review. No target runtime claim yet.
- Board identity/serial settings and explicit hardware authorization; no flashing,
  simulator or physical execution. M2b and all HAL work remain unverified.
- Full upstream compiler/LSP/sanitizer suites not run; scoped regressions only.
- Release license/distribution inventory and project license remain pending.
  SDK root Apache-2.0, example C CC0-1.0; component/tool licenses vary. Downloads
  and binaries ignored, not redistributed. Goose notices remain with patches.

## Files modified this task

New: tools/{esp_idf_baseline.py,esp-idf-pin.json,esp-idf-python.lock},
research/{ESP_IDF_BASELINE.md,esp-idf-baseline-results.json}.
Updated: tools/README.md, root README, AGENTS.md build pointer, architecture,
roadmap, decisions (008), learning notes, reference inventory, state and handoff.
No compiler/runtime patches or HAL implementation changes.

## Tests executed and results

- Official SDK clone/recursive pin and cleanliness checks: PASS, 25 submodules.
- install.sh esp32s3: PASS; exact-lock replay on existing installation: PASS.
- Official archive digest verification: PASS, six archives.
- python3 tools/esp_idf_baseline.py: PASS, activation and five recorded commands
  (package inventory, set-target, build, readelf, size); 543 top-level Ninja build
  steps plus bootloader. No warnings/errors detected in build/config logs.
- Source hash preservation, ELF identity, config/artifact checks, post-replay
  package equality: PASS. Five helper refusal paths: PASS. Python syntax and Git
  whitespace/local Markdown checks performed at final checkpoint.
- Earlier runtime checkpoint a66006f: 560 runtime commands incl. 496 arithmetic
  cases; validator 235 plus nested 19 host; historical validator-only 237;
  desktop runtime 32; scoped upstream CLI/JSON tests all PASS. Not rerun for
  SDK-only work because no Goose implementation changed.
- Goose Xtensa build / simulator / hardware / SDK panic adapter: NOT RUN / absent.

## Git and next actionable task

Branch main, no remote. Latest prior verified implementation:
a66006f33fea11078472a168c2037096f5c559ed (scalar runtime host gate).
The SDK checkpoint is the commit containing this file; resolve with git log -1
and verify status. Task changes intended to be committed together, leaving clean.
Ignored build/esp-idf-baseline contains full logs, ELF/map/images; tracked reviewed
results preserve hashes/versions even if cache is lost. Setup/build reproduction
is in tools/README.md. Fresh output required; helper refuses existing paths.

Next: inspect pinned ESP-IDF fatal-error API/startup/task ABI source, implement
minimal generated scalar leaf component and app_main/panic C bridge, cross-build
with this SDK, inspect symbols/map/assembly/native stack use. Keep codegen and
platform binding separate. Do not flash or begin HAL work.
Sol/medium for narrow component integration; Astra/high if panic/ABI/stack-safety
questions require deeper design. No model switch or hardware operation initiated.

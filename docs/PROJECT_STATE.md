# Project state

Updated 2026-11-05. Reconcile with Git/source. Current evidence:
[ESP32S3_SCALAR.md](../research/ESP32S3_SCALAR.md),
[esp32s3-scalar-results.json](../research/esp32s3-scalar-results.json).
Earlier compiler/runtime and SDK baseline reports remain in research/.

## Current milestone and task

M1 analysis complete. **M2a scalar leaf cross-build/ABI inspection gate complete**:
validator/runtime host gates, pinned official SDK baseline and generated leaf
firmware at -O0/-O2 pass. Current integration task complete. Whole-task stack
budget, target success/fatal execution and M2b remain unverified. No HAL.
Next: audit the remaining SDK/ROM stack paths, prepare stack measurement and
configuration-specific M2b records for the user's multiple board variants.

## Completed tasks

- Persistent agent instructions/skill, decisions, learning notes, roadmap and Git
  checkpoints established. Grapify unavailable in prior checks; standard tools.
- Clean official Goose pin 335fddc13dc74666398ffe160ec8a8f2958329d0; tracked patches
  0001/0002 and manifests enforce scalar-v0 and isolate runtime ABI 1. Compiler
  version 335fddc+scalar-v0-runtime, desktop runtime d22ae129d92b. Desktop remains
  default. No compiler/runtime patch changes in this task.
- Pinned ESP-IDF v6.0.2 / 7101770dc6db2667b3c477cc31365dd1acd6db4e, all 25 recursive
  submodules, tools.json/Xtensa GCC 15.2.0 (esp-15.2.0_20251204), 58 Python packages.
  Official baseline, archive hashes and existing-env locked replay pass.
- examples/esp32s3_scalar: CMake generates leaf C/header as a component; separate
  app_main checks scalar C ABI, calls init/ge_add(10,32)/exit and requests ROM
  console result output. Header generation precedes both C components.
- src/platform/esp_idf/scalar_panic.c: required noreturn hook records borrowed
  static diagnostic pointers/line in volatile storage and calls esp_system_abort.
  Compile guards enforce ABI 1 and minimal halt panic policy. No formatting or
  allocation in our adapter. Host double tests verify dispatch and pointer record.
- Cross-built both levels, inspected leaf/bridge object imports, final ELF/map/
  assembly and GCC static frame reports. Additional arithmetic fixtures compile
  for Xtensa as C11; no helper imports beyond the panic hook in tested objects.
- docs/HARDWARE_VALIDATION.md records per-board configuration/evidence workflow.
  User has several ESP32-S3 board types and wants eventual coverage across them;
  no exact board inventory/settings or hardware authorization supplied.

## Verified findings and limits

- Generated leaf/arithmetic object imports: exactly ge_scalar_v0_panic_v1, before
  linker GC and without LTO. Adapter imports: exactly esp_system_abort. Compiled
  SDK prefix reaches panic_abort/ill without allocator/formatter calls before
  the trap. Full SDK exception/console/boot paths are outside that claim.
- ABI assertions pass for i32 function prototype, byte/pointer/int widths and
  byte-aligned alias. Assembly shows windowed register calls/returns and aligned
  stack spills. No aggregate/reference/unaligned-buffer/MMIO portability claim.
- Leaf/bridge code in flash, static diagnostics in rodata; ready flag 4 bytes
  and panic record 12 bytes in internal DRAM BSS. SDK abort prefix in IRAM.
  No cache-off/ISR/reentrant/concurrent entry support.
- Image sizes: O0 145584, O2 145376 bytes; bootloader 21040, partition table 3072.
  Comparing to different hello_world logic/config is not Goose overhead isolation.
- Main-task config is 3584 bytes. Partial compiler-frame sums: normal arithmetic
  224/O0, 80/O2; overflow prefix through SDK trap 384/O0, 176/O2. NOT whole-task
  bounds: omit task entry, ROM printing, exceptions, register-window/interrupt
  effects and diagnostics. Hardware high-water use and complete budget unknown.
- Example explicitly selects print-and-halt and disables debugger-aware panic;
  minimal build omits optional trace/GDB-stub/core-dump components. Compile guard
  and probe reject enabled incompatible policies. Actual halt is unverified.
- SDK default DIO/2 MB/no-enabled-PSRAM/console settings are a control config,
  not a universal image for every module. Board settings stay out of the runtime.
- SDK/reference Goose checkouts clean. Binary hash recorded, but source/version
  checks alone do not prove arbitrary compiler binary provenance. No hermetic or
  bit-identical build claim; Python constraint drift remains a reviewed upgrade.

## Tests executed and results

- python3 tools/test_esp_idf_scalar.py --output build/esp-idf-scalar-verified:
  PASS, 53 commands including 14 expected failures; 547 top-level Ninja steps
  per target level plus bootloader. Code/input/artifact/SDK pin checks pass.
- 12 Linux bridge runs: two normal/restart cases, ten direct/cold/bad-init/
  overflow/after-exit fatal dispatch cases. Real adapter + terminating SDK double;
  no Xtensa execution. Adapter/host test compile -Wall -Wextra -Werror.
- Four compile refusals: wrong ABI and incompatible panic policy at each level.
- Three additional helper refusals: existing output, non-positive jobs and
  output overlapping prepared compiler source: PASS.
- Object dependencies/target flags, C11 arithmetic compile, final required symbols,
  ELF architecture, config, maps and assembly: PASS. GCC stack reports reviewed
  within partial scope above. No unknown config notes in verified run.
- Five generated unused helper/metadata warnings per level under existing SDK
  warning policy; no added suppression. No adapter/application warning detected.
- First configure failed on custom commands before SDK script-mode registration;
  corrected ordering. Earlier successful 39/51-command runs retained; unknown
  defaults discovered on review, removed and replaced by guard before final run.
- Python syntax, local Markdown and Git whitespace/integrity checks at final
  checkpoint. Earlier host 560 runtime/235 validator/32 desktop commands remain
  historical PASS; not rerun because compiler/runtime patches unchanged.
- Physical execution, simulator, serial output, full task stack: NOT RUN/unverified.

## Incomplete tasks / blockers

- Complete task-stack/SDK panic/ROM path budget and actual high-water measurement.
- Exact board settings and explicit hardware action authorization before flashing
  or monitoring. Success and fatal-policy physical cases require separate evidence.
- No M2b execution, HAL, peripheral/interrupt/concurrency implementation.
- Full upstream compiler/LSP/sanitizer suites and release license inventory pending.
  No project license selected; downloaded SDK/toolchain/generated artifacts ignored.

## Files modified and Git

New: examples/esp32s3_scalar/{CMakeLists.txt,sdkconfig.defaults,README.md,
components/goose_scalar/CMakeLists.txt,main/{CMakeLists.txt,app_main.c}},
src/platform/esp_idf/{scalar_panic.c,h}, tests/esp_idf/{panic_bridge_host.c,
stubs/{esp_system.h,sdkconfig.h}}, tools/test_esp_idf_scalar.py,
research/{ESP32S3_SCALAR.md,esp32s3-scalar-results.json}, docs/HARDWARE_VALIDATION.md.
Updated: README, src/tools READMEs, AGENTS build pointer, architecture, profile,
roadmap, decisions (009), learning notes, state and handoff. Compiler patches unchanged.

Branch main; no remote. Prior verified SDK checkpoint:
80043c9afa26d6d17e0a474329d9db8ae16e259e. Current integration checkpoint is the
commit containing this file; resolve git log -1 and verify status after commit.
Task changes intended to be committed together, leaving clean. Full logs/ELFs/
maps/configs in ignored build/esp-idf-scalar-verified; reviewed summary is tracked.

## Next actionable task and model

Audit SDK main-task/ROM/exception stack assumptions and prepare bounded stack
measurement in the example, plus a configuration-specific validation record.
Keep multiple-board settings explicit; do not invent module capabilities. Obtain
an identified board/configuration and explicit authorization before actual flash/
serial actions. No HAL before M2b. Sol/medium for measurement/config preparation;
Astra/high if stack/exception safety reasoning becomes a blocker. No model switch,
paid API or hardware operation initiated.

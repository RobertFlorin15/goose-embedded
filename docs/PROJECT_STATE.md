# Project state

Updated 2026-11-05. Reconcile with Git/source. Current evidence:
[STACK_MEASUREMENT.md](../research/STACK_MEASUREMENT.md),
[stack-measurement-results.json](../research/stack-measurement-results.json).
Historical integration, SDK baseline and compiler/runtime reports remain in research/.

## Current milestone and task

M1 analysis and M2a scalar leaf cross-build/ABI gate complete. Current task:
**normal-task stack observation code, SDK/ROM audit and host application tests
verified**. No physical execution/readings, simulator, full task stack bound or
HAL. M2b remains incomplete. Next: explicit board-configuration build inputs and
offline validation of configuration-specific run records/logs, keeping actual
hardware actions gated on identified configuration and authorization.

## Completed tasks

- Persistent agent instructions/skill, roadmap, architecture/decision/learning
  notes and Git checkpoints. Grapify unavailable in prior checks; standard tools.
- Goose pin 335fddc13dc74666398ffe160ec8a8f2958329d0 plus tracked patches 0001/0002
  enforce scalar-v0 and isolate runtime ABI 1. No compiler/runtime patch or panic
  implementation changes in this task. Desktop remains default and unchanged.
- ESP-IDF v6.0.2 / 7101770dc6db2667b3c477cc31365dd1acd6db4e, 25 recursive submodules,
  Xtensa GCC 15.2.0 (esp-15.2.0_20251204), official tools manifest and 58 Python
  package lock. SDK control and previous leaf builds pass; references clean.
- Leaf component generates profile C/header; app initializes/calls/checks/exits
  then requests ROM result printing. Versioned panic adapter records static
  source pointers and calls SDK abort; minimal halt-policy guard stays enforced.
- app_main now samples current-task lifetime byte low-water values before/after
  Goose, after result printing and after reporting. First three printed; all four
  and completed count in 20-byte volatile debugger record. No panic sampling.
- Pointer/prototype/layout assertions moved intact to target-only abi_checks.c,
  which target CMake/probe require. Actual app_main is host-tested with doubles
  without a macro bypassing target assertions. Byte/API/width guards stay in app.
- Audited SDK task parents, watermark helpers, exception dispatcher and ROM
  revision-0 printf code; individual frames and unresolved paths recorded.
- Per-configuration HARDWARE_RUN_TEMPLATE.md added. User has several ESP32-S3
  board types and wants eventual coverage across them; no exact inventory or
  board-specific settings/hardware action authorization has been supplied.

## Verified findings and evidence limits

- SDK API returns bytes for this port (StackType_t is uint8_t). Its fill-pattern
  scanner observes lifetime untouched space, not live SP or per-function usage;
  can miss untouched reserved frames. SDK startup/logging/measurement overhead
  is included. No arbitrary pass threshold or isolated Goose delta claim.
- completed=0..4 marks which sample fields are valid. Reset it at invocation;
  partial records cannot reuse stale fields. Post-report reading is debugger-only
  to avoid infinite measurement/reporting. No sample covers return logging/task
  deletion or a future fatal workload. No actual target readings exist.
- Visible frames: app_main 48, SDK main_task 48, wrapper 32; watermark API/current
  handle/scanner each 32 (helpers sequential). Partial arithmetic sums including
  parents: 304/O0 and 160/O2. Visible sampler path: 192. NOT task-stack bounds.
- User exception dispatcher allocates 192 bytes on task stack before C diagnostics.
  Ordinary interrupt dispatch later switches to RTOS stack; not interchangeable
  with panic entry. Window/context saves, nesting and SDK diagnostics remain open.
- Official revision-0 ROM ELF has print code (80/128/32-byte printf/vprintf/output
  frames) with indirect lock/putc callbacks and conversion paths. Actual callback
  and silicon/ROM configuration must be known for a complete bound.
- Main task still configured 3584 bytes; sufficiency not established. Default
  DIO/2 MB/no-enabled-PSRAM/console is a control configuration, not universal.
- Target generated leaf/arithmetic objects still import only panic hook; adapter
  only SDK abort. No LTO/section GC needed for object dependency claim. SDK boot/
  console/exception services are outside a firmware-wide no-allocation claim.
- Binary/source hashes retained, not proof of arbitrary compiler provenance or
  hermetic/bit-identical reproduction. SDK/Goose reference checkouts stay clean.

## Verification

- python3 tools/test_esp_idf_scalar.py --output build/esp-idf-stack-probe:
  PASS, 73 commands, 18 expected failures, both target levels. 548 top-level Ninja
  steps per firmware plus bootloader sub-builds. Earlier bridge/ABI/policy and
  arithmetic C11/dependency checks remain part of this run.
- Added actual app_main host-double tests at both levels: success with two
  invocations checks reset/phase/print order, exact units and post-report sample;
  wrong-result branch checks early fatal behavior. No RTOS/ROM execution.
- Simulated four-byte StackType_t rejected at both levels. Adapter and host
  application tests compile -Wall -Wextra -Werror. Target ABI witness compiled.
- Eleven supplementary static commands: five revision-0 ROM inspections, three
  SDK symbols per level. Frame/log/artifact/source hashes and 20-byte BSS record
  verified. Full raw logs remain under build/esp-idf-stack-{probe,audit}.
- Images O0 145888 / O2 145616 bytes; bootloader 21040, partition table 3072.
  Five known generated unused helper/metadata warnings per level; no new app
  warning or added suppression. No unknown config symbols in build logs.
- Python syntax, doc links, Git whitespace and evidence integrity checked at
  final checkpoint. Compiler/runtime implementation unchanged; broad historical
  host suites not rerun. Previous integration 53-command result remains historical.
- Physical success/panic, serial, simulator, full task budget: NOT RUN/unverified.

## Incomplete / blockers

- Complete SDK/ROM/callback/exception/register-window stack analysis and actual
  configuration/workload high-water evidence; measurements alone cannot prove bound.
- Exact board/flash/PSRAM/console settings and explicit authorization before any
  flash/monitor/debug operation. No M2b result, HAL or peripheral/concurrency work.
- Full upstream compiler/LSP/sanitizer suites, distribution inventory and project
  license remain pending. SDK/tool/generated artifacts ignored, not redistributed.

## Files and Git

New: examples/esp32s3_scalar/main/{abi_checks.c,stack_samples.h},
tests/esp_idf/{stack_samples_host.c,stubs/{esp_rom_sys.h,freertos/{FreeRTOS.h,task.h}}},
research/{STACK_MEASUREMENT.md,stack-measurement-results.json},
docs/HARDWARE_RUN_TEMPLATE.md. Updated: app_main/main CMake, target probe, example/
tools/root READMEs, hardware procedure, architecture/roadmap/decision/learning
notes and state/handoff. No changes to compiler patches or src platform panic.

Branch main; no remote. Prior verified integration:
cbebb2f660a4a9c8d02cc9003e0f5394d8039c4e. Current task checkpoint is the commit
containing this file; resolve git log -1 and verify status after commit. All task
changes intended to be committed together, leaving clean. Reproduce using
fresh output per tools/README.md; preserve reviewed historical results.

## Next action / model

Add explicit SDK configuration-overlay inputs and offline run/log validation
against reviewed build identity; keep per-variant records and no guessed boards.
Sol/medium suits these tools/tests. Astra/high is appropriate for closing the
whole task/exception/ROM stack-bound reasoning. No switch, paid API or hardware
operation initiated. Do not start HAL before physical M2b prerequisites pass.

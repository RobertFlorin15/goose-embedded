# Main-task stack audit and measurement preparation

2026-11-05. **Static target inspection, cross-compilation and host-double
execution only. No device/RTOS readings, serial session, simulator or flash.**

Starting checkpoint cbebb2f660a4a9c8d02cc9003e0f5394d8039c4e linked the scalar
leaf but left the whole native task stack budget open. This task audits the
omitted paths and prepares observations; it does not close that budget.
Pins remain Goose 335fddc13dc74666398ffe160ec8a8f2958329d0 plus unchanged
patches 0001/0002 and ESP-IDF 7101770dc6db2667b3c477cc31365dd1acd6db4e/v6.0.2.
GCC is esp-15.2.0_20251204 / 15.2.0; Python package lock unchanged.

## Instrumentation

Actual app_main now records four calls to uxTaskGetStackHighWaterMark(NULL):

| Field | Sampling point |
|---|---|
| before | Before Goose initialization |
| after_goose | After init/ge_add/check/exit |
| after_result_print | After the original result print |
| after_report | After printing the first three samples |

ge_stack_samples is a 20-byte volatile BSS record for debugger inspection, with
completed=0..4 identifying how many samples are valid. Reset completed before
each invocation; older values in unsampled fields are not valid. It is not
atomic or retained across reset. Only the first three readings are printed:

```text
goose-embedded scalar-v0: 42
goose-embedded stack-v1: before=N after_goose=N after_result_print=N bytes
```

N is a placeholder, not an observed value. The fourth is debugger-only to avoid
recursive measurement/reporting. app_main returns afterward; SDK return logging
and deletion are not covered. No measurements are added to the panic hook, where
assuming a working RTOS/task stack would broaden its safety assumptions.

The pinned [task.h](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/freertos/FreeRTOS-Kernel/include/freertos/task.h#L1490)
documents NULL as current task and byte units. In
[tasks.c](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/freertos/FreeRTOS-Kernel/tasks.c#L4807)
the scanner counts untouched fill bytes and divides by sizeof(StackType_t).
The pinned Xtensa port uses uint8_t StackType_t; FreeRTOSConfig.h enables the
API. Compile-time guards require this one-byte shape and API, and check sample/
console integer widths. Never multiply the returned value by four based on
generic FreeRTOS word-unit assumptions.

Scans are four fixed calls over a valid configured stack. They observe the
task's lifetime fill pattern, including SDK startup/logging, instrumentation and
incidental activity; they are not per-function live-stack readings. Reserved
but untouched frames and bytes coincidentally equal to the fill value can evade
this method. The observed workload is not a worst-case proof, and a high-water
delta is not isolated Goose consumption. No arbitrary pass threshold is chosen.

Target ABI assertions move intact to main/abi_checks.c, which CMake includes
and the target probe requires. This lets Linux tests execute the actual app_main
against doubles without a macro that disables target pointer-width checks.

## Audit of previously omitted paths

All function frame sizes below are **individual visible frames**, not inclusive
costs. SDK components retain their default SDK optimization, regardless of the
example's -O0/-O2 selection. Full target assembly logs are retained.

- [app_startup.c](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/freertos/app_startup.c#L176)
  logs/initializes services before app_main, then logs and deletes the task after
  return. Compiled main_task frame: 48 bytes. vPortTaskWrapper: 32 bytes and an
  indirect call to its task entry. Together add 80 visible parent-frame bytes.
  With unchanged app_main frame 48, the reviewed arithmetic path's frame sum is
  now 304/-O0 and 160/-O2 when including these parents. Still partial.
- Compiled uxTaskGetStackHighWaterMark, xTaskGetCurrentTaskHandle and
  prvTaskCheckFreeStackSpace frames are each 32 bytes. The first calls the latter
  two sequentially, not nested together. The visible sampler path including
  wrapper/main/app/API/one helper totals 192 bytes. It still has register-window,
  interrupt and untouched-frame caveats; the observation itself has overhead.
- The pinned
  [Xtensa vectors](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/xtensa/xtensa_vectors.S#L741)
  keep ordinary unhandled exceptions on the user/task stack. Compiled
  _xt_handle_exc subtracts 256 then adds 64: a 192-byte exception-frame
  allocation before context-save/C dispatch. Context save and window spills need
  their own accounting. Level-1 interrupt dispatch first allocates context, then
  enters the RTOS system stack; do not conflate that switch with the panic path.
- xt_unhandled_exception has a 32-byte entry frame and calls cache handling and
  panic processing. esp_panic_handler also has a 32-byte entry, then calls
  watchdog, formatting/console, state-dump callbacks and halt services. These
  frames are not the entire panic cost. The prior pre-trap sums (384/-O0 and
  176/-O2 excluding SDK parents) cannot be used as post-trap bounds.
- SDK ROM linker scripts map esp_rom_printf to a ROM entry stub. The official
  installed esp32s3_rev0_rom.elf contains actual code: its entry stub jumps to
  ets_printf. Visible frames: ets_printf 80, ets_vprintf 128, ets_write_char 32.
  Print-lock/unlock and character-output callbacks are indirect; integer
  conversion adds another path. A complete bound requires the actual callback
  configuration and matching silicon/ROM revision, not just these three frames.
  No particular user board revision has been identified.

The ROM ELF comes from the SDK-selected esp-rom-elfs 20241011 archive, previously
hash-verified in the SDK baseline. Its file hash and the static inspection
commands are preserved in the reviewed result summary. Addresses in audit logs
come from those artifacts; no hardware register addresses were invented.

## Verification

```sh
python3 tools/test_esp_idf_scalar.py --output build/esp-idf-stack-probe
```

**PASS: 73 commands, 18 expected failures**, including both target optimization
levels and existing ABI/panic/dependency checks. New host application tests use
deterministic SDK/Goose doubles: exact phase/print order and units, completed
reset across two invocations, post-report sample, and the wrong-result fatal
branch before further reporting. Synthetic test inputs 3000/2800/2400/2300 are
only host test data. Both levels also reject a simulated four-byte StackType_t.
The target-only pointer/prototype witness still compiles at both levels.

Target images: -O0 145888 bytes; -O2 145616. Bootloader 21040, partition table
3072. Both builds retain five known generated unused-helper/metadata warnings;
no new application warning or warning suppression. Generated leaf/arithmetic
imports stay exactly the panic hook; panic adapter still imports only SDK abort.
No compiler/runtime patch or panic-hook implementation changed.

Eleven supplementary read-only ROM/SDK disassembly commands pass (five ROM,
three SDK symbols per optimization level). Original/reference SDK and Goose
checkouts remain clean. Host checks never run a scheduler, ROM or Xtensa trap.
Reviewed evidence: [stack-measurement-results.json](stack-measurement-results.json).
Full logs/configs/maps and raw results remain in build/esp-idf-stack-probe and
build/esp-idf-stack-audit. Historical scalar target evidence remains in
[ESP32S3_SCALAR.md](ESP32S3_SCALAR.md).

## Remaining acceptance gate

Full SDK/ROM/exception/interrupt stack bound and physical readings remain open.
Do not claim the 3584-byte main stack sufficient from these partial sums. Use
the [run template](../docs/HARDWARE_RUN_TEMPLATE.md) for each reviewed board/config;
do not mark host-double values as measurements. User has several board types;
flash/PSRAM/console settings stay separate from the scalar runtime. No hardware
operation or HAL work is authorized by this checkpoint.

# Scalar-v0 linked for ESP32-S3

2026-11-05. **Target compilation/static inspection and Linux SDK-double tests
only. No simulator, physical execution, serial observation or flashing.**

The compiler/runtime patches are unchanged. Goose source pin
335fddc13dc74666398ffe160ec8a8f2958329d0 plus the two tracked patches produces
the library in examples/leaf.goose. SDK pin:
7101770dc6db2667b3c477cc31365dd1acd6db4e (ESP-IDF v6.0.2), Xtensa GCC 15.2.0
(esp-15.2.0_20251204). The reviewed official control build is in
[ESP_IDF_BASELINE.md](ESP_IDF_BASELINE.md).

## Implementation and verification contract

- examples/esp32s3_scalar has an ESP-IDF component that generates ge_leaf.c/h in
  the build tree using the opt-in scalar-v0 compiler. Generation precedes both
  component and main compilation; no generated runtime source is vendored.
- app_main checks ABI version, byte/pointer/integer widths, the byte-aligned
  gs_i32 alias and the ge_add prototype at compile time. It initializes, calls
  ge_add(10,32), checks 42, exits Goose, and requests a ROM console print.
- src/platform/esp_idf/scalar_panic.c defines the required noreturn ABI 1 hook.
  It stores borrowed static message/file/line in a debugger-visible volatile
  record, then calls esp_system_abort(message). No formatting, allocation or
  recovery. The record is neither atomic nor retained across reset; source
  location is available to a debugger rather than printed by this adapter.
- The example selects print-and-halt and disables debugger-aware panic handling;
  the minimal build omits runtime GDB stub, tracing and core dump components.
  The adapter rejects enabled incompatible policies at compile time; the probe checks sdkconfig
  and that LTO is disabled. Ordinary task/cache-enabled execution only. No
  interrupt entry, cache-off, simultaneous/reentrant callers or workers.
- The expected console line is `goose-embedded scalar-v0: 42`. This is a build
  input and future acceptance expectation, **not an observed serial result**.

Source/API evidence at the SDK pin:

- [esp_system.h](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/include/esp_system.h#L114)
  declares esp_system_abort noreturn; its
  [implementation](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/port/esp_system_chip.c#L85)
  calls panic_abort. [panic.c](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/panic.c#L461)
  retains the message, triggers Xtensa ill, then has an infinite-loop fallback.
- The [fatal-error guide](https://docs.espressif.com/projects/esp-idf/en/v6.0.2/esp32s3/api-guides/fatal-errors.html)
  describes configurable halt/reboot/debugger behavior. The binding delegates
  fatal handling to that SDK path, not a custom CPU startup/exception handler.
- [app_startup.c](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/freertos/app_startup.c#L176)
  calls app_main from its normal main task and deletes the task after return.

## Reproduce

Follow tools/README.md for the pinned compiler/SDK first. Use a fresh output:

```sh
python3 tools/test_esp_idf_scalar.py --output build/esp-idf-scalar-verified
```

The helper verifies the clean SDK/gitlinks, tools manifest, installed Python
lock, patched source digests and compiler version; records the compiler binary
hash (source checks alone cannot prove its binary provenance); builds at Goose
and component -O0/-O2; inspects non-LTO objects and linked firmware; compiles
additional arithmetic C11 objects; runs host bridge tests and retains logs.
Reviewed result summary: [esp32s3-scalar-results.json](esp32s3-scalar-results.json). Generated C/header, objects,
ELF/map/assembly/config/logs remain in the ignored output tree.

The first attempt failed during requirements discovery because add_custom_command
preceded idf_component_register, which ESP-IDF substitutes in script mode. Moving
non-scriptable commands after registration fixes the cause. The next build
(build/esp-idf-scalar-2) passed 39 commands. Additional bridge-dependency,
optimization/ABI rejection and SDK disassembly checks motivated the final fresh
build (build/esp-idf-scalar-final, 51 commands). Review then found three unknown
config symbols: their components are absent from the minimal build, so assigning
defaults had no effect. Removed those assignments, added a compile-time panic
policy guard plus negative test, and ran a fresh verified build. These attempts
and corrections are retained in ignored logs; no compiler checks were weakened.

Final verified run: **PASS, 53 commands**, including 14 expected failures. Both
firmware configurations complete 547 top-level Ninja steps plus bootloader
sub-builds. Twelve Linux bridge runs cover normal computation/restart and direct,
cold-call, bad-init, overflow and after-exit panic dispatch at each level. Four
compile refusals cover wrong adapter ABI and incompatible panic policy. Three
additional helper checks refuse existing output, non-positive jobs and output
overlapping compiler source (separate from the 53-command run). The
adapter/test C compile with -Wall -Wextra -Werror on the host. Target SDK flags
use GNU C23; standalone arithmetic objects compile as strict C11. Five known
generated-C unused-helper/metadata warnings occur per level under SDK warning
flags; no added suppression, and no adapter/application warning or unknown
configuration note remains in the verified build.

| Final artifact | -O0 bytes | -O2 bytes |
|---|---:|---:|
| Application image | 145584 | 145376 |
| Bootloader | 21040 | 21040 |
| Partition table | 3072 | 3072 |

Both app images fit the default 1 MiB app partition with 86% free. Baseline
hello_world was 145424 bytes, but it has different application logic/panic
settings; these differences are not isolated Goose overhead measurements.
SDK/reference Goose checkouts remain clean. Existing broad host compiler/runtime
suites were not rerun: patches unchanged; this task adds targeted bridge tests.

## Static ABI, dependency and stack review

The following findings apply to the tested leaf and arithmetic fixtures, not
the whole Goose language or every possible scalar-v0 source.

- At -O0 and -O2, generated leaf and arithmetic objects have only
  ge_scalar_v0_panic_v1 undefined, before linker garbage collection. No malloc,
  VM, signal, pthread or libgcc helpers are referenced by these objects.
- The real platform adapter object has only esp_system_abort undefined. Its
  assembly consists of normal aligned stores into the diagnostic record and
  the SDK call. The compiled SDK prefix calls panic_abort, sets SDK diagnostic
  state and executes ill; there are no allocator/formatter calls before that
  trap. This does not audit every SDK exception/console/boot path or prove a
  firmware-wide no-allocation property.
- Linked app_main passes 10/32 to ge_add via the Xtensa windowed C calling
  convention; ge_add receives scalar arguments in a2/a3 and returns in a2,
  with call8/retw and aligned frame spills. No hidden Goose data-stack argument
  appears at the public boundary. At -O2 widened addition and overflow checks
  remain in ge_add, including the branch to the versioned panic hook.
- No caller-provided unaligned buffer is accessed by the leaf. Scalar register
  arguments and natural stack slots avoid an unaligned-memory test here;
  byte-aligned aliases are not evidence for aggregates/references/MMIO support.
- Map/assembly place example/export code in flash text, static error strings in
  flash rodata, the ready flag (4 bytes) and panic record (12 bytes) in internal
  DRAM BSS. The SDK abort prefix is in IRAM. These are linked placements, not
  measured hardware availability or a cache-off safety claim.

GCC -fstack-usage reports these static frame sizes:

| Function | -O0 bytes | -O2 bytes |
|---|---:|---:|
| app_main | 48 | 48 |
| ge_add | 48 | 32 |
| add_g | 64 | inlined |
| gs_add_i32 | 64 | inlined |
| gs_scalar_overflow | 48 | inlined |
| ge_scalar_v0_panic_v1 | 48 | 32 |
| goose_init | 48 | 32 |
| goose_exit | 32 | 32 |

Reviewed disassembly additionally shows 32-byte frames each for SDK
esp_system_abort and panic_abort. Adding compiler frame sizes along the normal
app_main -> ge_add arithmetic path gives 224/-O0 and 80/-O2 bytes; the overflow
path through the SDK prefix up to the trap gives 384 and 176 respectively.
These are **partial call-path sums**, not a task-stack bound: exclude SDK task
entry, ROM printf, exception handling, register-window/interrupt effects and
SDK diagnostics. Main-task stack is configured as 3584 bytes. Its full budget
and actual high-water use remain unverified; do not infer sufficiency by simply
subtracting the partial sums from that setting.

## Remaining gates

Physical execution of success and fatal cases, actual serial/halt behavior,
whole task stack budget/high-water measurement and board/flash/console settings.
No hardware action until a concrete board/configuration is reviewed and explicit
authorization exists. M2b remains incomplete and HAL work remains blocked.
The user has multiple ESP32-S3 board types and wants eventual coverage across
them; [HARDWARE_VALIDATION.md](../docs/HARDWARE_VALIDATION.md) separates shared
runtime from configuration-specific validation. No exact board has been chosen.
The current leaf cross-build/ABI inspection gate is satisfied with these limits;
no general target-language/runtime portability or real-time guarantee follows.

New project C/CMake/Python code uses SDK APIs without copying SDK implementation.
Generated Goose runtime retains upstream Apache-2.0 provenance; downloaded SDK,
toolchains and generated artifacts remain ignored. Release license inventory and
project license selection remain pending.

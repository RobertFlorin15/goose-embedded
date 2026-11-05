# ESP32-S3 scalar proof of concept

Build-only proof of Goose-generated scalar-v0 C linked with pinned ESP-IDF
v6.0.2. Hardware execution is not yet verified. No HAL, pin control or interrupts.

Prepare the compiler/SDK using [tools/README.md](../../tools/README.md), then:

```sh
python3 tools/test_esp_idf_scalar.py
```

The helper requires a fresh output directory, verifies SDK/source/package pins,
and builds this example at Goose/component -O0 and -O2 with no LTO. It also runs
Linux tests of the real panic adapter against a terminating SDK double. No
hardware port is opened. Use --output build/esp-idf-scalar-new if output exists.

The goose_scalar component runs the prepared host compiler as a CMake generation
step on examples/leaf.goose. Generated C/header live in the component's build
directory. The main component depends on generation, checks the scalar C ABI,
calls goose_init(0, NULL), ge_add(10, 32), checks 42, then goose_exit. The expected
ROM console line is `goose-embedded scalar-v0: 42`; it has not been observed on
a device. Returning from app_main lets ESP-IDF delete its main task.

app_main samples its task's lifetime minimum untouched stack space before Goose,
after Goose, after result printing, and after reporting the first three readings.
Units are bytes in the pinned Xtensa port. The first three appear in a
`goose-embedded stack-v1:` line; the fourth is debugger-only in
ge_stack_samples.after_report, with completed=4 marking the full record.
Target ABI checks are in abi_checks.c; host application tests use SDK/Goose
doubles. No actual hardware readings or worst-case stack proof exist yet. See
[stack audit](../../research/STACK_MEASUREMENT.md) and
[run template](../../docs/HARDWARE_RUN_TEMPLATE.md).

The platform panic adapter retains borrowed static message/file/line in the
debugger-visible ge_scalar_v0_last_panic record and calls esp_system_abort with
the unchanged message. It performs no formatting or allocation. Source location
is retained for inspection, not printed by this adapter. The SDK owns the
non-returning fatal path. sdkconfig.defaults selects print-and-halt and disables
debugger-aware handling. The minimal build omits runtime GDB stub, tracing and
core dump components; the adapter rejects enabled incompatible policies at compile
time. Actual config is checked by the helper. This is an ordinary-task/cache-enabled example only;
the crash record is not atomic or a concurrent/ISR facility, and does not survive
reset. SDK startup/console/panic services are outside a firmware-wide no-heap
claim. Physical panic/halt behavior and full task stack budget remain unverified.

For manual builds use an activated SDK child shell, a fresh external build
directory and external SDKCONFIG, with -DGOOSE_COMPILER pointing to the prepared
compiler and -DGE_SCALAR_OPT=0 or 2. The helper is the verified workflow. Do not
flash until the board/configuration is reviewed and hardware operation authorized.

Flash/PSRAM/console settings belong to each board configuration, not to the
scalar runtime. The current 2 MB/DIO build setting is not a claim about every
ESP32-S3 module. See [hardware validation](../../docs/HARDWARE_VALIDATION.md).

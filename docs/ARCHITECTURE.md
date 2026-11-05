# Architecture

## Verified upstream structure

At pin 335fddc13dc74666398ffe160ec8a8f2958329d0, a C++20 host compiler
lexes/parses Goose into AST, resolves names, typechecks/specializes functions,
optimizes specialization ASTs, performs bounds-check analysis, and emits C.
The driver either invokes host TinyCC, invokes an external host C compiler,
or writes C for another build system. There is no Xtensa backend in this
traced path. Full source evidence: [feasibility report](../research/FEASIBILITY.md).

The target boundary is generated C plus runtime. Internal ABI includes hidden
data-stack indices/destination parameters. Export wrappers and --header provide
a C ABI and goose_init/goose_exit lifecycle. Host lifecycle/restart is tested;
Xtensa scalar leaf ABI is compile-checked and assembly-reviewed; physical
lifecycle execution is unverified.

Upstream runtime comprises runtime.h (configuration/types/inlines),
runtime_impl.h (memory/errors/printing), runtime_threads.h, runtime_ext.h
(FFI types/declarations/helpers), runtime_os.h (OS primitives). Compiler embeds
canonical runtime files in runtime_inline.h. Its data-stack growth assumes
stable reserved addresses and protected gaps; C heap allocations exist in
metadata/lifecycle/error/thread paths. Pointer layouts are modeled as 64-bit
in parts of codegen. Zero reported regions does not bypass runtime startup.

## Project boundaries

1. Compiler adaptations: explicit target layout, restricted feature profile,
   checked memory lowering; prefer narrow upstream-compatible changes.
2. Embedded runtime: lifecycle, bounded storage and overflow-before-write,
   diagnostics and unsupported-feature rejection; separate from hardware.
3. ESP32-S3 platform: ESP-IDF app_main bridge, build/link/runtime integration,
   narrow C wrappers for SDK services and later MMIO.
4. Portable HAL contracts: based on Goose's actual function/generic/ADT
   capabilities after source verification, not simulated Rust ownership/traits.
5. Drivers: use those contracts; no platform registers in portable logic.
6. Application libraries/examples: robotics and learning-oriented programs.

Initial target hypothesis: export leaf i32 addition from Goose, call via C
app_main in one ESP-IDF RTOS task, print result using C SDK console facilities.
No direct Goose ISR entry, Goose worker threads, reentrant runtime, dynamic
libraries, or growable values in this first proposed subset. The scalar-only runtime now has a versioned panic interface, verified on hosts;
no data-stack arena exists. The minimal ESP-IDF panic binding is target-linked
and host-stub tested; physical execution remains unverified.

Static data must fit measured DRAM/IRAM budgets; native call-stack use must fit
configured RTOS task space; generated C packing/alignment and scalar helper
semantics must be checked with the target compiler. Reducing reserve macros
alone does not satisfy these conditions. ESP32-S3 flash MMU/cache features do
not establish the desktop VM protocol required upstream.

No HAL, register map, allocator replacement or async executor exists. The
unchanged official ESP32-S3 control and scalar leaf builds pass; simulator and
hardware results remain pending. Preserve that evidence
boundary in public descriptions.

## Scalar profile design checkpoint

[SCALAR_PROFILE.md](SCALAR_PROFILE.md) specifies the next opt-in compiler/runtime
adaptation. Its compiler validator and isolated scalar runtime are implemented
and host-tested; leaf target compilation/linking now passes. It narrows initial support to i32 C exports,
scalar locals/expressions and acyclic direct calls/if/return, with a structural
allowlist and checked arithmetic. All imports, foreign calls, recursion,
references/aggregates, loops and user globals are initially rejected by design.
A separate codegen invariant must establish zero main/global/worker regions.

[Runtime startup measurements](../research/RUNTIME_STARTUP.md) establish that
zero regions still allocate metadata, install signal facilities, query thread
stack attributes, and acquire shutdown locks in the separate desktop runtime.
The scalar path now bypasses both inline lifecycle and emitted desktop teardown;
replacing only external gs_rt_start would have been insufficient. A platform panic hook must
preserve failed-init/export-guard and overflow behavior without desktop services.

## Implemented compiler validation boundary

patches/goose/0001-scalar-v0-validator.patch adds the explicit profile option,
pre-typecheck source allowlist and acyclic-call validation, post-typecheck
scalar/call checks before optimization, and post-codegen zero-region/unsupported
state invariants. Ast carries a default-off parse policy so imports/namespaces/
extern blocks are rejected before package loading; root sidecars are rejected
before interpretation. Ordinary parsing/typechecking/codegen and runtime code
remain unchanged when the option is absent. Profile C forces GS_DEBUG=1.

The helper prepares a fresh git archive at the pin, applies the tracked patch,
checks file digests and records provenance. Outputs are staged and individually
renamed only after validation; consumers must honor failure status and serialize
writers. This first patch remains independently reproducible with --validator-only;
current preparation also applies the second runtime patch. See research/SCALAR_VALIDATOR.md for evidence.

## Isolated scalar runtime ABI 1

Patch 0002 selects canonical runtime_scalar.h only for validated scalar programs,
without runtime_ext/desktop headers. It emits cold/ready state transitions with
zero-region compile-time assertions and rejects all argc/argv combinations other
than 0/NULL. Checked arithmetic uses the same widened i32 rules; failures,
including codegen unreachable guards, call ge_scalar_v0_panic_v1. The platform
supplies this non-returning hook. GE_SCALAR_V0_ABI_VERSION=1 identifies it; export
symbols starting ge_scalar_v0_ are reserved. No heap, VM, signal or thread setup
is selected. The Linux host hook remains test code; the ESP-IDF example uses its own SDK
binding in src/platform/esp_idf/scalar_panic.c.

The scalar section is included in runtime_inline.h by upstream regeneration,
with a separate ABI version domain so the unchanged desktop sections retain
their d22ae129d92b hash. Native/generated objects and generic i386 freestanding
objects have only the hook unresolved at both -O0/-O2, with no LTO/section GC;
selected lifecycle API counters remain zero. Desktop output is byte-identical
and its behavioral regressions pass. See research/SCALAR_RUNTIME.md for bounds
on those host observations. The leaf target evidence is below; hardware
verification remains open.

## Verified SDK control build

ESP-IDF v6.0.2 at 7101770dc6db2667b3c477cc31365dd1acd6db4e and its 25 recursive
submodules are pinned; tools.json selects Xtensa GCC 15.2.0. Official tools are
project-local; the Python package list has a separate lock because upstream
constraints update independently. tools/esp_idf_baseline.py builds an unchanged
hello_world in a fresh ignored output tree and records source/artifact hashes,
configuration, versions, ELF header and size. The control ELF links as 32-bit
little-endian Xtensa; no Goose code is in it. Defaults include a 3584-byte main
task stack, whose sufficiency for the upcoming scalar adapter remains unknown.
See research/ESP_IDF_BASELINE.md. The platform boundary is now implemented for
the scalar leaf as described below.

## ESP-IDF scalar integration (cross-built, not physically verified)

examples/esp32s3_scalar/components/goose_scalar generates profile C/header through
the host compiler into the CMake build tree, then compiles it with the platform
panic binding. The separate main component checks the scalar C prototype/layout,
initializes, calls ge_add, checks 42, exits, prints through the SDK ROM API and
returns to the SDK main task. No replacement startup or extra Goose task exists.

src/platform/esp_idf/scalar_panic.c owns ge_scalar_v0_panic_v1: store the static
diagnostic pointers/line in a 12-byte volatile target record, then directly call
the SDK's noreturn esp_system_abort. Compile-time guards require ABI 1 and the
reviewed minimal print-and-halt policy. No formatting/recovery/allocator in the
adapter. This record is not a concurrent crash log; the contract is one normal
task with caches available. The SDK owns exception/console/boot services.

At -O0/-O2 generated leaf/arithmetic objects require only the hook; adapter
requires only esp_system_abort. No LTO or section GC is needed for that object
evidence. Final ELF/map/assembly and static ABI assertions pass. Compiler frame
sums cover only partial paths, not the full 3584-byte main-task stack budget or
actual high-water use. Physical success/fatal behavior remains unverified.
See research/ESP32S3_SCALAR.md for warnings, sizes and source-backed limits.

User has several ESP32-S3 board variants. Keep flash/PSRAM/console settings in
explicit SDK configurations and future board/pin mappings outside the portable
runtime. No exact board inventory is supplied; the current DIO/2 MB/no-PSRAM
control build is not a universal image. docs/HARDWARE_VALIDATION.md defines the
per-configuration evidence record. No HAL or physical action follows this build.

## Stack observations (prepared, not physically collected)

The example records four current-task lifetime low-water byte values via the
pinned FreeRTOS API: before/after Goose, after result printing and after report
printing. The first three are printed; all four plus completed count remain in
the 20-byte volatile ge_stack_samples record. No sampling is added to panic.
Target ABI checks remain in a separate compiled witness. Linux tests execute
the actual application with SDK/Goose doubles, without bypassing target asserts.

The SDK scanner counts fill bytes; Xtensa StackType_t is one byte. Scanning can
miss untouched reserved frames and does not establish worst-case behavior.
Visible main-task/wrapper frames add 80 bytes above app_main. User exception
handling allocates a 192-byte task-stack frame before C diagnostics; ordinary
interrupt dispatch later switches stacks. Revision-0 ROM print code has indirect
callbacks and additional frames. Complete stack/exception bounds remain open.
See research/STACK_MEASUREMENT.md and docs/HARDWARE_RUN_TEMPLATE.md. No actual
reading, validated board configuration or physical success claim follows.

## Configuration and capture boundaries

The scalar probe snapshots ordered SDK defaults plus .esp32s3 siblings before
configuration. Explicit IDs label the requested configurations; effective SDK
config and all image/ELF hashes are retained in a per-level run manifest. Known
target/panic/LTO policy and unknown-symbol checks precede build. Snapshots and
hashes support repeatability but do not automatically include files referenced
by arbitrary SDK options or certify a board's flash/PSRAM/console capabilities.

The example converts the full SDK app descriptor ELF digest into fixed static
hex storage and prints identity before sampling. It prints a completion marker
after the fourth sample; that last print and SDK return are outside observations.
Compiler/runtime/panic implementations stay unchanged. No Goose foreign API or
HAL feature is added by this C application instrumentation.

tools/validate_scalar_run.py checks only saved-file consistency: local artifacts,
capture/manifest hashes, config/level, firmware identity, ordered normal telemetry,
known failure/reset cues and sample shape/ranges. It always reports physical
execution and stack bounds as unproven. Real module identity, authorization and
physical evidence remain a human/measurement boundary. See RUN_LOG_FORMAT.md and
research/CONFIGURATION_LOG_VALIDATION.md; current automated captures are synthetic.

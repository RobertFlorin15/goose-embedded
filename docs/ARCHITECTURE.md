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
Xtensa lifecycle/ABI is unverified.

Upstream runtime comprises runtime.h (configuration/types/inlines),
runtime_impl.h (memory/errors/printing), runtime_threads.h, runtime_ext.h
(FFI types/declarations/helpers), runtime_os.h (OS primitives). Compiler embeds
canonical runtime files in runtime_inline.h. Its data-stack growth assumes
stable reserved addresses and protected gaps; C heap allocations exist in
metadata/lifecycle/error/thread paths. Pointer layouts are modeled as 64-bit
in parts of codegen. Zero reported regions does not bypass runtime startup.

## Project boundaries (runtime/platform/HAL implementation pending)

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
no data-stack arena or ESP32-S3 platform binding exists.

Static data must fit measured DRAM/IRAM budgets; native call-stack use must fit
configured RTOS task space; generated C packing/alignment and scalar helper
semantics must be checked with the target compiler. Reducing reserve macros
alone does not satisfy these conditions. ESP32-S3 flash MMU/cache features do
not establish the desktop VM protocol required upstream.

No HAL, register map, allocator replacement or async executor exists. The
unchanged official ESP32-S3 SDK control build passes; Goose target compilation,
simulator and hardware results remain pending. Preserve that evidence
boundary in public descriptions.

## Scalar profile design checkpoint

[SCALAR_PROFILE.md](SCALAR_PROFILE.md) specifies the next opt-in compiler/runtime
adaptation. Its compiler validator and isolated scalar runtime are implemented
and host-tested; target compilation is pending. It narrows initial support to i32 C exports,
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
is selected. The host hook is test code, not an ESP-IDF adapter.

The scalar section is included in runtime_inline.h by upstream regeneration,
with a separate ABI version domain so the unchanged desktop sections retain
their d22ae129d92b hash. Native/generated objects and generic i386 freestanding
objects have only the hook unresolved at both -O0/-O2, with no LTO/section GC;
selected lifecycle API counters remain zero. Desktop output is byte-identical
and its behavioral regressions pass. See research/SCALAR_RUNTIME.md for bounds
on those observations; Xtensa and hardware verification remain open.

## Verified SDK control build

ESP-IDF v6.0.2 at 7101770dc6db2667b3c477cc31365dd1acd6db4e and its 25 recursive
submodules are pinned; tools.json selects Xtensa GCC 15.2.0. Official tools are
project-local; the Python package list has a separate lock because upstream
constraints update independently. tools/esp_idf_baseline.py builds an unchanged
hello_world in a fresh ignored output tree and records source/artifact hashes,
configuration, versions, ELF header and size. The control ELF links as 32-bit
little-endian Xtensa; no Goose code is in it. Defaults include a 3584-byte main
task stack, whose sufficiency for the upcoming scalar adapter remains unknown.
See research/ESP_IDF_BASELINE.md. The platform boundary is still pending; no SDK
fatal-error binding or generated scalar component has been added yet.

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

## Intended project boundaries (not implemented)

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
libraries, or growable values in this first proposed subset. No arena strategy
or target-runtime interface is implemented or finalized yet.

Static data must fit measured DRAM/IRAM budgets; native call-stack use must fit
configured RTOS task space; generated C packing/alignment and scalar helper
semantics must be checked with the target compiler. Reducing reserve macros
alone does not satisfy these conditions. ESP32-S3 flash MMU/cache features do
not establish the desktop VM protocol required upstream.

No HAL, register map, allocator replacement or async executor exists. Target
builds, simulator and hardware results are all pending. Preserve that evidence
boundary in public descriptions.

## Scalar profile design checkpoint

[SCALAR_PROFILE.md](SCALAR_PROFILE.md) specifies the next opt-in compiler/runtime
adaptation; it is not implemented. It narrows initial support to i32 C exports,
scalar locals/expressions and acyclic direct calls/if/return, with a structural
allowlist and checked arithmetic. All imports, foreign calls, recursion,
references/aggregates, loops and user globals are initially rejected by design.
A separate codegen invariant must establish zero main/global/worker regions.

[Runtime startup measurements](../research/RUNTIME_STARTUP.md) establish that
zero regions still allocate metadata, install signal facilities, query thread
stack attributes, and acquire shutdown locks in the separate desktop runtime.
Therefore both the inline lifecycle and emitted teardown need restricted paths;
replacing only external gs_rt_start is insufficient. A platform panic hook must
preserve failed-init/export-guard and overflow behavior without desktop services.

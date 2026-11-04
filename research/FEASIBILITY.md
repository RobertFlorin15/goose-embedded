# Goose on ESP32-S3: first feasibility report

Date: 2026-11-04. M1 analysis complete; embedded execution unverified.

## Initial M1 conclusion and evidence boundary (historical)

A restricted Goose program appears technically plausible on ESP32-S3 through generated C and ESP-IDF. This is a hypothesis supported by source inspection and successful Linux host experiments, not a target build or hardware result. The full desktop runtime cannot be assumed portable. Two primary obstacles are guarded virtual-memory data stacks and fixed 64-bit layout assumptions. No compiler patch, embedded runtime, HAL, flash operation, or hardware execution has been performed.

Goose was inspected and built at **335fddc13dc74666398ffe160ec8a8f2958329d0**, runtime version **d22ae129d92b**. `upstream.json` is the machine-readable pin. Local downloaded source is ignored under `.cache/goose`; setup is in [tools/README.md](../tools/README.md). Source links below are immutable at this revision. Other ecosystem references are dated architectural readings of moving branches, not build dependencies.

## Compiler architecture and module relationships

The [driver](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/main.cpp#L1580) establishes this pipeline:

| Stage | Actual source | Role and embedded relevance |
|---|---|---|
| Lexing | `src/lexer.h` | Hand-written token scanner. No target change identified. |
| Parsing/imports | `src/parser.h`, `src/ast.h` | Recursive descent; AST and top-level registration. Imports/packages are host concerns. |
| Type name resolution | `src/resolve.h`; driver `ResolveTypeNames` | Resolve names before checking. |
| Type/lifetime checking | `src/typecheck.h`, `typecheck_{types,exprs,flow,calls,builtins,nodes,expansion}.h` | Specializes functions; tracks roots, growth and escape effects. Preserve these checks. |
| Optimization | `src/optimize.h`, `optimize_{basecase,tre,loops,reassoc}.h` | Rewrites checked specialization bodies in place. |
| Bounds check elimination | `src/bce.h` | Runs before C generation; any embedded capacity checks need a separate sound proof before elimination. |
| C generation | `src/codegen.h` and `codegen_*.h` | Consumes optimized `FnSpec::body`; computes types, frames, values, construction, calls, statements, stack bounds, exports. |
| Assembly of C/runtime | driver around lines 1695–1735 | Prepends runtime sections and generated types/program. Separate runtime is default; standalone emits all runtime code. |
| Host execution/linking | `src/jit.h`, `build.h`, `native.h`, `toolchain.h`, `process.cpp` | TinyCC in-process run or external host C compiler; not an ESP-IDF cross-build abstraction. |

There is a typed/specialized AST representation (`FnSpec` bodies), not an LLVM backend in this traced path. The optimizer and backend consume that representation directly. [CodeGen's overview](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/codegen.h#L1) explains hidden stack arguments, in-place return destinations, and scope watermark restores. This is the architectural map obtained with `rg` and direct source reads; it is not a Grapify graph.

Compiler implementation is C++20. [CMake](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/CMakeLists.txt) builds the host compiler and its TinyCC/shader dependencies. [libtcc.cmake](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/cmake/libtcc.cmake#L16) accepts x86-64/arm64 hosts. Keep the compiler on the development host; the firmware needs generated C and a target runtime, not TinyCC or the C++ compiler itself.

## Runtime and memory model

Source: [runtime.h](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/runtime/runtime.h), [runtime_impl.h](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/runtime/runtime_impl.h), [codegen.h](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/codegen.h).

- Native C call stack, static globals, and compiler-assigned data stacks coexist. Large fixed locals may also use data stacks: fixed size alone does not establish zero regions.
- Dynamic values are inline byte images; resizable values have a base/count header and a stack top. Growth does not relocate the base. Scope exits restore saved tops rather than traverse/free individual elements.
- Internal stack-using calls receive a hidden `int64_t gs_sp`; dynamic results receive destination stacks. Public C exports have wrappers, distinct from this internal ABI.
- Default `GS_STACK_RESERVE` is 2 GiB per region, gap 1 MiB, budget 32 TiB. These are virtual address reservations, not physical RAM consumption on Linux. Smaller flags do not remove OS dependencies or add software bounds checks.
- POSIX implementation uses `mmap`, `mprotect`, signal handlers/alternate signal stack, `munmap`, and native-thread stack discovery. Windows uses `VirtualAlloc` and exception handling. See runtime_impl.h around 440–600, 642–715 and 1480–1530.
- **No general-purpose allocator for Goose values does not mean no C heap use.** `gs_stack_block` calls `calloc` even for zero stacks (`runtime.h:1028`); region metadata uses `calloc`; error formatting and alternate signal stacks use `malloc`. Thread queues allocate nodes. This runtime is not verified heap-free.
- Type/root checking protects lifetimes; capacity, slice, division and related runtime checks protect other operations. Some checks are debug-only (`GS_DEBUG`). Unbounded data-stack growth relies on the reserved region/guard mechanism. Replacing it with a small unchecked static array would allow writes beyond the arena.
- `runtime_os.h` includes filesystem, dynamic-library, time and platform services. Threaded execution additionally needs TLS and pthread/Windows thread/queue operations (`runtime_threads.h`). Disable or reject unsupported features in a future target profile rather than silently stub successful behavior.
- Runtime files in `src/runtime/` are canonical. `src/runtime_inline.h` embeds them in the compiler; upstream `--gen-runtime-header` regenerates it. Runtime modifications must update the embedded copy and runtime version consistently.

## 32-bit layout and ABI obstacle

[codegen_types.h:245–315](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/codegen_types.h#L245) returns 8 for ordinary reference size/alignment, 16 for slices and resizable references. Emitted packed C uses real pointers (`{ uint8_t *data; int64_t len; }`, and two-pointer `gs_rref`).

On the tested x86-64 host these sizes agree. A freestanding `cc -m32` witness verifies packed slice = 12 bytes, two-pointer reference = 8 bytes, pointer = 4. This demonstrates a discrepancy with the hard-coded model on a 32-bit C ABI; it does not yet demonstrate a particular miscompiled Xtensa program. Audit all fixed sizes, offsets, pointer serialization, reference pools and wrappers before allowing those features. Scalar-only exports avoid much of the exposed layout, but do not prove the rest of the translation unit portable.

Goose deliberately emits byte-aligned scalar aliases and packed aggregates. GCC support on the host is verified; target Xtensa assembly and unaligned-access behavior remain to be checked. Foreign struct and slice ABI must be verified from generated headers and target compiler output, not inferred from same-named C types. Native register MMIO must remain in a narrow C platform boundary until volatile semantics and access widths are established.

## ESP32-S3 integration requirements

The [official datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) describes 32-bit LX7 processors and 512 KiB SRAM; that total is not available application memory. [ESP-IDF memory documentation](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/memory-types.html) describes shared IRAM/DRAM budgets, external memory, and flash MMU/cache behavior. These facilities do not establish support for Goose's desktop anonymous-memory reservation and POSIX fault-handling protocol. Do not describe this chip simply as having “no MMU.”

[ESP-IDF startup](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/startup.html) reaches `app_main` in an RTOS task. Its [component build system](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/build-system.html) can compile C files into component libraries. Inference: an `app_main` C adapter calling a Goose export is a smaller initial integration than replacing startup or porting the compiler to Xtensa. These moving `stable` documentation URLs resolved to v6.1 during research; no ESP-IDF release is selected or installed for this project yet.

Upstream `--header` already suppresses generated C `main` and exposes `goose_init`, `goose_exit`, and named exports. Host restart testing passes. However, every generated initializer calls `gs_rt_init`, even a library reporting zero regions; its runtime still initializes page sizing, region metadata and native-stack machinery. A target profile must handle that lifecycle explicitly.

Interrupts and multicore reentrancy are not established. Start with one RTOS task calling Goose, no callbacks from interrupts, no Goose workers and no shared mutable Goose state. Do not assume an ESP-IDF pthread subset implements the needed desktop interfaces.

## Experiments and smallest candidate subset

See [EXPERIMENTS.md](EXPERIMENTS.md) and tracked [host-results.json](host-results.json).

- Release host compiler configured/built successfully with warnings.
- Arithmetic/assert/print application emitted and executed through GCC: `goose-embedded: 42`; one data region.
- Growable `u8` array application: `growth: 32`; two data regions.
- C host library invocation, shutdown and restart succeeded twice.
- `leaf.goose`, exporting only i32 addition and no main, reported **zero** data-stack regions; C host invocation/restart passed, still using the desktop runtime.
- 32-bit packed-layout witness compiled successfully without 32-bit libc.

Candidate: explicitly sized integers/bools, scalar-only exports and internal scalar functions, bounded nonrecursive control flow, scalar C externs if separately verified. Initially exclude references/slices/aggregates crossing C, resizable or large fixed values, dynamic libraries, OS APIs, threads, interrupts, async and recursion. No claim yet that this subset is enforced by the compiler or sufficient for target execution. Keep all safety checks required by supported operations.

## Primary blockers and proof-of-concept plan

| Blocker | Evidence | Smallest next verification |
|---|---|---|
| Desktop runtime initialization and virtual memory | Source + generated leaf initializer | Design explicit zero-region target runtime profile; enumerate actual linked symbols; fail closed for unsupported features. |
| 32-bit pointer/layout mismatch | Hard-coded sizes + -m32 witness | Inventory target-dependent sizes; add target layout model before enabling references/aggregates. |
| Target C code/ABI/alignment | Not yet compiled for Xtensa | Pin official ESP-IDF/toolchain; compile leaf-generated C and inspect errors, ELF and assembly. |
| Memory budget | No target map/stack measurements | Record flash/IRAM/DRAM map and RTOS native-stack high-water use after a target build/run. |
| Hardware execution | No board/serial session verified | After build and explicit hardware-operation authorization, call export from app_main and print/check 42 on serial. |

1. Review restricted-profile safety and ABI design; no guessed allocator replacement.
2. Implement the minimum opt-in zero-region runtime adaptation and rejection rules, separate from HAL; test host lifecycle and rejection cases.
3. Install/pin ESP-IDF in a project-local environment; build its known example before combining with Goose. Record target selection (`esp32s3`) and exact compiler version; tool names vary by release, so inspect rather than assume.
4. Compile generated leaf library as an ESP-IDF component, call lifecycle/export from app_main, inspect unresolved symbols and final sections. Successful target linking is a separate acceptance gate.
5. With board details and explicit operation authorization, flash/monitor a serial check of result 42. Record board, wiring, firmware SHA, command and serial log. Only then claim M2 execution.
6. Expand to bounded memory with overflow-before-write guarantees; postpone portable HAL until the runtime contract and hardware proof exist.

## Follow-up design checkpoint

The subsequent [startup inventory](RUNTIME_STARTUP.md) traces the separate
runtime at -O0/-O2 and the [scalar-v0 specification](../docs/SCALAR_PROFILE.md)
defines a compiler-enforced restricted profile. The later [validator checkpoint](SCALAR_VALIDATOR.md) implements profile
enforcement and host rejection tests. Target-runtime adaptation remains pending. These follow-up results refine
the initial plan without changing its host-only evidence boundary.

## Reference ecosystems and license boundary

[REFERENCES.md](REFERENCES.md) records the five requested projects and preliminary license observations. No Rust, ESP-IDF or Goose implementation code was copied into tracked project files; generated C remains ignored. Framework license is deliberately pending a dependency/distribution inventory, including bundled compiler third parties.

Grapify was absent from `/home/robert/.agents`, `/home/robert/.codex/skills`, `/home/robert/.codex/plugins` by case-insensitive filename search, and absent from available tool metadata. No Grapify instructions or commands were invented. Recheck availability in future environments.

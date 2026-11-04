# Scalar-v0 runtime ABI 1 — host verification

2026-11-05 (work began 2026-11-04). This checkpoint implements the restricted runtime after the
[validator checkpoint](SCALAR_VALIDATOR.md). No ESP-IDF installation, Xtensa
compile, simulator, physical run or HAL implementation was performed.

## Implementation and reproducibility

[0002-scalar-v0-runtime.patch](../patches/goose/0002-scalar-v0-runtime.patch)
applies after the unchanged validator patch to Goose
335fddc13dc74666398ffe160ec8a8f2958329d0. The
[runtime manifest](../patches/goose/runtime-manifest.json) records both the
validator dependency and final file digests. Preparation verifies each stage
before recording provenance; --validator-only retains the first-stage behavior.
Canonical runtime_scalar.h and the upstream-regenerated runtime_inline.h are
included in the patch, so clean preparation needs one normal compiler build.

The initial development tree .cache/goose-scalar-runtime was prepared from
patch 0001, extended, bootstrapped, regenerated with upstream --gen-runtime-header,
and rebuilt. The final patched generator reproduces runtime_inline.h byte for
byte. Original .cache/goose and all existing canonical desktop runtime files
remain unmodified.

The compiler selects runtime_scalar.h only after source/type validation and
zero-region/unsupported-state invariants pass. runtime_ext.h is not supplied to
scalar codegen; it no longer emits unused FFI/slice/builder types into scalar C.
The generated C embeds checked i32 helpers, source-location strings and a
cold/ready flag. It never selects runtime.h, runtime_impl.h, runtime_threads.h
or runtime_os.h. No stack block/region allocation, dummy arena or OS stub exists.

The arithmetic rules preserve upstream's widening to int64_t for i32 add/sub/
mul/neg, range checking before narrowing, and non-returning overflow behavior.
This wide type suffices for every intermediate product of two i32 values. Unlike
the full runtime, the subset does not include float, division or arbitrary
integer-width helpers. Checked unreachable-code guards emitted even at -O0
also forward to the platform panic hook, rather than assuming undefined behavior.

## Public C contract

Generated headers declare:

```c
#define GE_SCALAR_V0_ABI_VERSION 1
/* Declared noreturn using the compiler's supported attribute. */
void ge_scalar_v0_panic_v1(const char *message, const char *file, int line);
void goose_init(int argc, char **argv);
void goose_exit(void);
/* Plus the admitted scalar exports. */
```

The platform supplies the hook; no fallback is linked. It must never return,
allocate, recover with longjmp, re-enter Goose or call unsupported runtime
services. Message/file are borrowed static strings; file is NULL and line 0
for lifecycle failures. Arithmetic/unreachable failures supply source file and
positive line. Returning from the hook violates the C noreturn contract; no
recovery after panic is supported. A future ESP-IDF binding must be explicitly
implemented/verified, not inferred from this host adapter.

The host-only test hook uses unformatted write/_Exit diagnostics. It checks
observer state before exiting and validates location shape. It is not firmware.
Export C symbols starting with ge_scalar_v0_ are reserved to avoid collision
with the panic ABI. Missing/v2 hooks fail to resolve the required v1 symbol;
incompatible ABI macros and disabled arithmetic checks fail compilation.

Lifecycle, serial access from one normal caller/task only:

- goose_exit while cold is harmless.
- Export while cold (including after exit) panics.
- goose_init accepts only argc=0, argv=NULL, sets ready with no external calls.
- Repeated valid init while ready is harmless; invalid arguments panic even
  while ready. Checking arguments precedes the idempotence guard.
- Successful exports compute normally; goose_exit clears ready and permits
  restart. No allocator/free, fault installation or teardown is involved.
- Concurrency, ISR entry, callbacks and multiple simultaneous program instances
  remain outside the supported calling contract; no cross-task detector exists.

Generated C asserts zero main/global/worker regions and an 8-bit byte/32-bit i32
model. GS_SCALAR_V0_VALIDATED=1 still identifies validator revision 1;
GE_SCALAR_V0_ABI_VERSION=1 and ge_scalar_v0_panic_v1 identify the separate runtime
ABI. The desktop RuntimeVersion deliberately excludes the independent scalar
section: its unchanged sections still hash to d22ae129d92b, preserving desktop
object compatibility. Scalar ABI changes need their own reviewed version change.

## Commands and results

The final compiler reports `goose 335fddc+scalar-v0-runtime (runtime d22ae129d92b)`.
GCC 15.2.0/CMake 4.2.3/Ninja 1.13.2 were used; Clang version is in the archived
summary. Use the exact commands in [tools/README.md](../tools/README.md).

```sh
python3 tools/test_scalar_runtime.py --compiler build/goose-scalar-runtime/goose
python3 tools/test_scalar_validator.py --compiler build/goose-scalar-runtime/goose
python3 tools/runtime_probe.py --compiler build/goose-scalar-runtime/goose
```

- Runtime suite: **560 commands match expected status**, including 179 expected
  exit-1 cases. **496** deterministic arithmetic input cases (248 per level)
  match Python arbitrary-precision results or expected overflow. Edge pairs
  include INT32_MIN/MAX, zero, -1, 46340/46341; random pairs use seed 0.
- At Goose/native -O0 and -O2, the accepted control-flow library and the separate
  arithmetic library compile/link/run with no desktop runtime object, -lm,
  -pthread, section garbage collection or LTO.
- Each native generated object has exactly one undefined symbol:
  **ge_scalar_v0_panic_v1**. Four generic i386 freestanding Clang objects also
  have exactly that symbol; these are compilation evidence, not execution or
  Xtensa ABI evidence. No aggregate/reference model is being tested/enabled.
- Clean host executable symbols contain no selected forbidden direct imports.
  Test harness/libc startup and diagnostic imports remain and are not Goose
  runtime dependencies. Instrumented executables separately include the observer
  itself, so their complete link-symbol lists are not used as the clean proof.
- Two init/compute/exit cycles plus duplicate/cold calls yield 11 phases per
  level; every counter is zero for all 14 selected allocation/VM/signal/pthread
  APIs. Pre-init/post-exit, bad argc/argv/ready arguments and four arithmetic
  failure paths invoke the hook with expected diagnostics and no selected calls.
- Missing/wrong hook version fails linkage; ABI macro mismatch, tampered GS_DEBUG
  and nonzero-region static assertions fail compilation. These deliberately
  altered C artifacts test defenses, not acceptance of arbitrary edited C.
- Frontend suite: **235** top-level commands pass (209 expected failures), plus
  the nested original **19-command** desktop host probe. It retains all 46 source
  rejection cases and output/CLI/preparation checks. Two prior --emit-runtime
  commands are no longer needed in runtime mode; --validator-only retains the
  earlier 237-command workflow, which also passed again in this task. Reserved panic symbol is checked by runtime tests.
- Separate desktop runtime suite: **32** commands pass, including the original
  allocation/signal/thread observations and six expected failures. Normal mode
  still reports/uses its desktop facilities; scalar changes do not silently
  substitute a restricted runtime in ordinary Goose programs.
- Scoped pinned upstream CLI path and structured JSON diagnostic suites pass.
  With stdlib installed beside the new compiler, use the harness documented in
  SCALAR_VALIDATOR.md with the new executable/source paths.
- Emitted desktop --emit-runtime C is **byte-identical** to the validator-stage
  compiler output. Existing desktop runtime files are byte-identical to the pin.
- Final --gen-runtime-header is byte-idempotent; Python syntax, C host warnings,
  file/patch digests, local documentation links and Git whitespace are checked.

[scalar-runtime-results.json](scalar-runtime-results.json) preserves reviewed
counts, phase/symbol evidence, versions and patch digests. Detailed local command
logs are build/scalar-runtime-tests/results.json, scalar-validator-tests/results.json
and runtime-probe/results.json under build/.

## Scope of the memory/OS claim

The generated scalar objects' only external dependency is the audited platform
hook on the tested native and generic i386 builds. Their lifecycle has no data
regions or heap metadata. Direct-call observation supports that structural
result for the exercised paths. The 14 wrapped APIs are not an exhaustive OS
API catalog, and linker wrapping does not observe shared libc internals. This
is not a claim that a host/ESP-IDF process allocates nothing, that any arbitrary
user hook is safe, or that all possible scalar programs have been verified.

A finite acyclic source call graph still consumes native stack. Generic i386
compile success is not Xtensa execution, IRAM/DRAM sizing, ISR safety, multicore
safety or a physical measurement. Those gates remain pending. The next task is
to pin an official ESP-IDF/toolchain and prove its unchanged baseline build,
then compile a generated leaf component and inspect target symbols/maps/assembly.

## Corrective findings

The first emitted scalar C revealed that codegen emits GS_UNREACHABLE guards
at -O0 even after an explicit return. Added a checked forwarding macro to the
same versioned panic boundary, regenerated embedded text and rebuilt. No unchecked
fallback or silent compiler warning suppression was used. The first generated
second-patch diff also lacked new-file metadata; strict preparation rejected it.
Added the metadata and verified complete fresh source reproduction. Both were
corrected before final successful logs; desktop sources were never modified.

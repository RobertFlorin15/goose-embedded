# Scalar-v0 target profile design

Status: validator implemented and host-tested, 2026-11-04. **Runtime adaptation
is still pending.** The tracked Goose patch enforces the scalar subset and emits
checked C using the desktop runtime. This is not MCU firmware support.
Source baseline: 335fddc13dc74666398ffe160ec8a8f2958329d0. Supporting measurements:
[separate-runtime investigation](../research/RUNTIME_STARTUP.md).

## Objective and acceptance boundary

Compile a C-callable i32 Goose library for ESP32-S3 with zero data regions,
no Goose runtime heap allocation, and no desktop OS services. Start with
examples/leaf.goose. Keep upstream desktop behavior unchanged unless the new
profile is explicitly selected. The first implementation is host-tested;
Xtensa build and hardware execution are later independent gates.

A zero stack count is necessary and insufficient. Foreign calls, reference
parameters and recursion all pass that metric in upstream; GS_MAX_STACKS=0
actually disables its limit. Neither this flag nor a text scan of generated C
is an acceptable implementation of profile enforcement.

## Supported source contract

The validator uses an explicit allowlist; every unrecognized node/declaration,
operator or concrete type is rejected with a source diagnostic. Start smaller
than the long-term embedded language subset:

| Area | Accepted in v0 | Rejected in v0 |
|---|---|---|
| Program form | One explicit library root, at least one named C export | Goose main, imports/packages, user include headers/native sidecars, standalone/JIT/run/build modes |
| Functions | Top-level, explicitly typed, non-generic scalar functions returning i32; direct calls to other accepted functions | externs (including scalar), dynamic externs, nested/function-valued/higher-order functions, recursion, SIMD and special function modifiers |
| Public ABI | Explicit i32 parameters and i32 result, generated export header | bool or other-width integer exports initially; references, slices, structs, arrays, ADTs and multiple returns |
| Local data | i32 and bool locals; representable integer constants, boolean literals | Globals, static user storage, strings, all aggregate/reference/variable-size data, floating point, varint, other integer widths, casts |
| Expressions | Scalar identifiers; i32 +, -, *, unary negation; comparisons; boolean !, &&, ||; ordinary local assignment | Division/remainder/shifts/bit operations initially; address/dereference/index/slice/field operations; all builtins, including print/assert/abort/OS/thread operations |
| Control flow | Blocks, if/else, ordinary return to current function | All loops, recursive cycles, return-from/nonlocal control, lambdas/compile-time expansion |

Literal syntax and compiler-internal metadata need not be i32 machine values;
all evaluated integer storage/operations in the admitted program must be i32.
The typed validator must check actual specialization/node types rather than
assume explicit parameter annotations constrain every expression. Bool is only
an internal/local control value in this version; never a foreign ABI promise.

Reject disallowed constructs even if unused or removed by optimization. Source
functions must be validated before optimization, including uncalled helpers;
compiler-created builtin/type catalogs are not themselves user declarations.
No silent acceptance via inlining, constant folding or dead-code elimination.
Acyclic calls plus no loops give finite structural control flow for each export,
but do not prove that its native stack fits the configured RTOS task.

## Compiler integration and validation order

Implemented interface: `--embedded-profile=scalar-v0`, in explicit C emission/
library mode with --header and -o. See tools/README.md for preparation and tests.
GS_SCALAR_V0_VALIDATED=1 marks validator revision 1, not an embedded runtime ABI.
The option is a host compiler feature; a C macro alone does not select or prove
validation. All user -D options are rejected and GS_DEBUG=1 is forced.

1. Parse options and reject conflicting modes, native packages/includes and
   attempts to turn off required checks. Force GS_DEBUG=1; reject GS_DEBUG=0,
   unsupported stack/runtime/SIMD defines, and unsafe checking overrides.
2. Inspect parsed user declarations/bodies before typechecking/optimization:
   explicit declaration/node/operator allowlist, no imports, main or forbidden
   constructs, even in uncalled functions or statically false branches.
3. Keep ordinary name resolution/type/root checking. Inspect checked
   specialization bodies before Optimizer: admitted concrete types/calls only,
   no foreign/builtin calls, no recursive call-graph SCC (including self-edge).
   Resolve/reject modifiers and generic inference explicitly. Ast/FnSpec metadata
   supplies evidence; do not scan source text for keywords.
4. Reuse codegen stack accounting, then assert main stacks == 0,
   globalregions == 0, workerregions == 0, no threads/queues/dynamic bindings,
   no data-stack-dependent exports and no unsupported generated state. This
   is a second invariant check, not a substitute for the source validator.
5. Current validator assembles the normal separate desktop runtime declarations
   and generated library only after all checks pass. Restricted runtime
   assembly remains the next change. C/header writes are staged and individually
   renamed; a pair is not a filesystem transaction. Validation failure preserves
   prior outputs, staging failure cleans temporary files, and publication failure
   invalidates the header. Use a fresh build directory, one writer per output
   pair, and never consume artifacts from a failed command. Input/output aliases
   and pre-existing staging paths are rejected.

Implemented frontend seams: main.cpp's option parsing and
pipeline around TypeCheckProgram/Optimizer; default-off parser policy in Ast;
source/typed walkers in scalar_profile.h; existing CodeGen stack accounting is
queried without changing its implementation. Runtime adaptation will later touch
EmitProgramInit/EmitExports and canonical runtime files/embedded copy. The
reviewable patch, digests and upstream license are in patches/goose/.
If upstream behavior/catalogs make this validation impractical, narrow the
allowlist further instead of weakening its checks.

## Runtime lifecycle

Preserve public goose_init/goose_exit and the existing guard on exports.
Host owns one instance and calls it serially from one normal RTOS task. No
reentrancy, interrupt entry, callbacks or concurrent callers are supported;
this is a documented calling contract, not an implemented cross-task detector.

| State/action | Required result |
|---|---|
| Cold -> goose_exit | No-op |
| Cold -> exported function | Non-returning platform panic |
| Cold -> goose_init(0, NULL) | Initialize synthetic generated state, become ready; no VM, heap, signal or pthread setup |
| Ready -> goose_init(0, NULL) | No-op |
| Ready -> export | Compute checked i32 result |
| Ready -> goose_exit | Clear instance state, become cold; no allocator/free/OS teardown |
| Cold after exit -> export | Non-returning platform panic |
| Cold after exit -> init | Same behavior as first init |

Initially accept only argc=0, argv=NULL; reject other argument combinations
through the panic boundary because this subset has no argument/OS API. Guard
against impossible nonzero region/thread counts with a compiler invariant and
compile-time evidence in emitted C; never silently allocate or ignore them.

The static gs_rt_init currently calls both gs_rt_start and gs_stack_block;
replacing only external gs_rt_start cannot remove calloc. Likewise generated
goose_exit currently frees gs_stks. Both emitted/inlined paths need explicit
restricted branches. Do not fake a valid gs_stack with a null top or allocate
a token arena. No data-stack access is legitimate in this profile.

Retain upstream scalar arithmetic helpers and debug overflow semantics.
Provide the exact reachable failure functions (currently gs_panic, gs_ovf for
leaf addition; gs_ovf_neg for permitted negation must be verified), forwarding
to one original, small non-returning platform panic hook with constant category
and source location. The hook must not depend on heap formatting, signals,
longjmp, workers or dynamic libraries. Do not include runtime_impl.h,
runtime_threads.h or runtime_os.h in the target runtime artifact. Reuse of
runtime.h requires reviewing/branching its static lifecycle code, not pretending
that a linker flag disables unsupported language features.

Host tests use a deterministic exit hook; a later ESP-IDF adapter must select
and verify its supported non-returning panic/abort mechanism. No error recovery
or re-entry after panic is promised. Profile v0 always keeps checked arithmetic;
normal desktop release behavior remains unchanged.

## ABI, linker and memory obligations

- Check CHAR_BIT=8, sizeof(int32_t)=4, and the actual exported C prototype using
  compile-time assertions/generated declarations. Validate target assembly for
  byte-aligned scalar aliases. Do not impose sizeof(void*)=8 on the target.
- User reference/aggregate data is forbidden; synthetic unused pointer type
  declarations in the current generated header are not a claim of supported
  32-bit layouts. Do not permit their instantiation in a user program.
- Give the profile/runtime contract an explicit version marker. Keep upstream
  runtime_inline.h regeneration/hash consistent with canonical files. A target
  artifact must identify source pin, profile version and required panic ABI.
- Optimization and section garbage collection may reduce unused helpers.
  Neither proves the source profile. Check final linked symbol/section evidence
  at -O0 and -O2 against the profile's documented runtime/compiler-support and
  platform-hook dependencies. Object-file undefined references and dynamically
  executed functions are different evidence sets.
- “No heap” applies only to profile-generated lifecycle/computation/failure hook,
  not to ESP-IDF, libc, boot or the host process as a whole. Prove it with the
  restricted host artifact and symbol/call traces; current desktop measurements
  below do not satisfy this goal.
- Native call depth is finite but still requires target map/stack analysis.
  Record actual task stack use once hardware tests exist. No footprint or
  timing guarantee is established by the design.

## Implementation acceptance tests

Frontend tests pass as recorded in research/SCALAR_VALIDATOR.md. The runtime
and target obligations below remain pending:

1. Leaf library succeeds with -O0/-O2 and overflow checks, with identical scalar
   results; an ordinary desktop library retains its existing behavior.
2. For the restricted artifact, lifecycle sequence above is allocation/VM/
   signal/pthread-free under direct-call instrumentation and link inspection.
   Repeated init/exit and restart work; pre-init/post-exit calls and overflow
   trigger the deterministic host panic hook. Confirm subtraction/multiplication/
   negation edge cases if admitted by the implementation.
3. Source rejection fixtures cover every forbidden category, unknown/unhandled
   AST forms, unused helpers and optimized-away false branches at both levels.
   The test runner now rejects their equivalent sources along with unused/dead
   code cases. profile_candidates remain baseline acceptance fixtures for the
   older separate-runtime probe.
4. Reject conflicting flags, altered pins/runtime contracts and nonzero
   main/global/worker counts. Failed commands cannot supply new build artifacts.
5. Regenerate embedded runtime text and run upstream tests appropriate to changed
   compiler/runtime paths. Prove clean desktop behavior as well as target-mode
   behavior; scope the suite according to the actual patch.
6. Only after these host gates, pin an official ESP-IDF release/toolchain, build
   its baseline and the library component, inspect Xtensa ELF/ABI/sections.
   Physical serial result 42 remains a separate authorized hardware gate.

## Alternatives and consequences

A standalone C shim plus regex filtering is smaller, but cannot establish the
source/type/optimization invariants. A replacement gs_rt_start alone misses
inline calloc and generated free. A fixed unchecked data arena would weaken
safety. A full 32-bit layout/runtime port is broader than needed for first scalar
execution. Select compiler-enforced scalar-v0 plus narrow lifecycle/failure
adaptation; retain these broader paths as future work after the first proof.

## Current verification boundary

The validator rejects 46 source fixtures plus a sidecar at both -O0/-O2,
conflicting CLI actions/defines, source/output aliases and bad preparation pins.
Typed arithmetic and stored values are scalar; representable literal arithmetic
may fold during typechecking before the typed walk (verified with 1 + 2).
Forced checked C executes on the host, including arithmetic failure paths.
No runtime files were modified or regenerated. The allocation-free lifecycle,
panic hook, target ABI and Xtensa execution described above are still requirements.

# Decision log

## 001 — Host AOT compiler, ESP-IDF target integration (2026-11-04)

Problem: reach ESP32-S3 without porting development tools to the chip.
Alternatives: port compiler/TinyCC, write machine-code backend, generate C and
reuse ESP-IDF. Selected: investigate host-generated C with ESP-IDF. Rationale:
upstream C emission and export lifecycle exist and work on host; IDF supplies
startup/linking. Tradeoff: runtime and ABI portability remain our work; using C
is not a target compatibility proof. Consequence: no on-device compiler/JIT.

## 002 — Prove a restricted scalar subset first

Problem: guarded VM growth and hard-coded 64-bit pointer sizes block a full
runtime port. Alternatives: small unchecked static arenas; full runtime rewrite;
restricted zero-region profile then incremental safe expansion. Selected:
design the restricted profile first. Evidence: leaf export reports zero regions,
but still calls runtime init. Rationale: minimizes initial semantics and exposes
startup obstacles. Tradeoff: no useful dynamic data or HAL yet. Consequence:
profile enforcement, lifecycle adaptation and target compiler validation must
precede any claim of support. Exact enforcement design is next work, not done.

## 003 — Preserve safety when bounding memory

Problem: desktop growth can bump pointers with no per-write arena check.
Alternatives: rely on MCU faults/canaries; insert checks; statically forbid
unproven growth. Selected constraint: before supporting data stacks, check every
relevant write before it occurs or prove sufficient capacity for that subset.
Rationale: after-write canaries and guessed guard behavior cannot preserve
memory safety. Tradeoff: performance/implementation cost; checks require overflow-
safe arithmetic. Consequence: no static-buffer drop-in runtime replacement.

## 004 — Pinned evidence; license decision deferred

Problem: moving upstream and compiler third parties obscure reproducibility
and redistribution obligations. Selected: pin Goose, keep downloads/generated
C ignored, record source links and license observations; defer project license
until concrete dependency/distribution review. Alternative: vendor compiler or
pick a license from the root README alone. Tradeoff: not ready for public release
yet. Consequence: preserve attribution when future code is copied/distributed.

## 005 — Enforce scalar-v0 in the compiler, not via stack flags (2026-11-04)

Problem: zero-region programs can still contain C externs, references and native
recursion, and GS_MAX_STACKS=0 disables the upstream stack limit. Separate-runtime
startup and teardown retain allocation/signal/pthread dependencies even with no
regions/workers, verified by direct-call observation at -O0/-O2.
Alternatives: GS_MAX_STACKS flag only; regex scan or symbol-only acceptance;
replacement gs_rt_start; full runtime/layout port; compiler structural/type
allowlist plus separate count invariants and restricted lifecycle.
Selected design: [scalar-v0](SCALAR_PROFILE.md), compiler enforcement before
optimization, zero-region verification after codegen accounting, explicit
allocation-free lifecycle and non-returning platform panic boundary. Initially
restrict even loops and scalar foreign calls to bound the proof surface.
Rationale: preserve safety without inventing bounded arenas or letting optimizer
choices decide source acceptance. Tradeoffs: a narrow experimental subset and
compiler/runtime patch maintenance; target ABI and stack budget remain separate
proofs. Consequence: no profile implementation claim until rejection, lifecycle,
failure and desktop regression tests pass. This session commits design/probes only.

## 006 — Ship validation before runtime adaptation (2026-11-04)

Problem: a source profile must be enforceable independently of a replacement
runtime, without allowing optimization or parser package-loading side effects
to choose acceptance. Selected: an opt-in compiler patch with parsed AST and
pre-optimization checked-specialization walks, a source call-graph cycle check,
and existing codegen count/state invariants. Reject imports/directives during
parsing, sidecars before interpretation, and CLI conflicts before early-return
actions. Default-off Ast policy preserves the existing ParseProgram API used
by LSP and roundtrip callers. Ordinary compiler behavior remains available.

Alternatives: change ParseProgram's public signature; post-emission filtering;
combine runtime work into the same patch. The signature change caused ambiguity
with its LSP declaration in an initial build; preserving the API removes that
regression surface. Literal arithmetic can fold during typechecking; retain
source structural checks while allowing checked representable literal results.

Consequences: profile output deliberately uses the unmodified desktop runtime
and a validation-only version marker. No target or allocation-free claim.
Per-file staged output replacement cannot atomically publish a two-file snapshot;
callers must use fresh outputs, serialize writers and honor exit status. Reject
source/output aliases and avoid publishing output before profile checks pass.

## 007 — Isolate the scalar runtime section (2026-11-04–05; host-verified)

Problem: even unused static helpers in full runtime.h emit heap/VM/math references
at -O0; replacing gs_rt_start alone leaves inline calloc and generated free.
Selected: add a canonical runtime_scalar.h section for the enforced subset,
containing the same widened checked i32 add/sub/mul/neg rules and a required
versioned non-returning panic hook; profile codegen emits its own cold/ready
lifecycle and never selects desktop runtime sections. Normal codegen/runtime
remain the default. No arena, dummy stack or silently successful OS stubs.
Tradeoff: a small subset of upstream arithmetic rules must be kept in parity;
verify boundary behavior at both optimization levels. Use an independent scalar
ABI marker/hook version; keep the desktop runtime hash tied to its unchanged
sections. Regenerate the compiler's embedded runtime text from canonical files.
Target and hardware verification remain separate gates.

Verification for decision 007: 560 runtime commands, 235 current validator
commands plus nested desktop probes, and the 32-command desktop runtime probe
pass. Exact source/object/observation limits are in research/SCALAR_RUNTIME.md.
Target toolchain and physical measurements remain separate gates.

## 008 — Pin ESP-IDF and build a control application first (2026-11-05)

Problem: host scalar tests do not establish an ESP32-S3 build environment, and a
first build containing both new runtime and new SDK integration would confound
failures. Selected: ESP-IDF v6.0.2 at commit 7101770dc6db2667b3c477cc31365dd1acd6db4e,
its pinned tools.json (Xtensa GCC 15.2.0), and unchanged official hello_world as
the control build. It is an officially documented stable bugfix release, selected
explicitly rather than following a moving release branch.

Alternatives: an older 5.x SDK, moving master, system SDK, or immediately linking
Goose. None gives this project a stronger verified baseline yet. A project-local
legacy install.sh/export.sh workflow avoids changing the host configuration or
adding EIM as another installation dependency; the official v6 guide continues
to document that method. Tradeoffs: larger cached SDK/tools and manual release
upgrades; Python dependencies need their own recorded versions because upstream
constraints can refresh independently of the SDK commit. Check hashes and retain
logs; do not promise byte-identical builds from just a Git revision.

Acceptance/results: research/ESP_IDF_BASELINE.md. After the control build passes,
add only the scalar leaf component and app_main/panic bridge. No physical result,
HAL support or target runtime safety follows from the control application alone.

## 009 — Use the SDK fatal boundary and keep board settings separate (2026-11-05)

Problem: the generated library requires a non-returning panic hook and a C ABI
caller; host behavior alone cannot establish the Xtensa integration. Selected:
separate generated and main components using ESP-IDF startup; a tiny platform
hook records borrowed static diagnostics and calls esp_system_abort directly.
Select print-and-halt, forbid enabled tracing/GDB-stub/core-dump/debugger-aware
policies with a compile guard, and retain source location for debugger inspection.
The minimal build lacks the optional components, so do not assign unknown Kconfig
symbols as if they enforced a policy. No formatting or heap use in our hook.

Alternatives: custom assembly trap (bypasses supported SDK diagnostics), formatted
abort message (adds formatting/storage obligations), ROM print before abort
(adds another panic-path service), or silently ignoring failure (violates runtime
safety). The direct supported API has the smallest source-backed boundary.
Tradeoffs: console prints the message but our file/line record needs a debugger;
the SDK's full exception handling and actual physical halt/stack usage still need
verification. Keep cache-disabled/ISR/concurrent entry unsupported.

The user wants future coverage across multiple ESP32-S3 board types. Separate
chip/runtime logic from board-specific flash/PSRAM/console/pin configurations;
require per-configuration build/execution evidence, not a universal binary claim.
No guessed board definitions. Proof: cross-build/ABI/object/map/assembly and host
SDK-double tests in research/ESP32S3_SCALAR.md; physical execution remains open.

# Scalar-v0 validator implementation checkpoint

2026-11-04. Scope: opt-in compiler validation and rejection tests **before**
runtime startup adaptation. Evidence level: Linux x86-64 host only. No Xtensa
build, simulator, hardware operation, target runtime or HAL implementation.

## Deliverable and provenance

Tracked implementation: [compiler patch](../patches/goose/0001-scalar-v0-validator.patch)
against Goose 335fddc13dc74666398ffe160ec8a8f2958329d0. Patch/file SHA-256 values
are in [manifest.json](../patches/goose/manifest.json); upstream Apache-2.0 license
and modified-file notices accompany it. [Preparation helper](../tools/prepare_scalar_compiler.py)
uses a clean pinned git archive, applies and verifies the patch, and records
provenance. Original .cache/goose remains clean and unmodified.

The implementation lives in a disposable .cache/goose-scalar development tree
and was built in build/goose-scalar. A clean archive+patch preparation reproduced
all four changed/new compiler files exactly; the test runner repeats this check.
Runtime files (including runtime_inline.h) and codegen implementation files are
unchanged; existing CodeGen counters/state are queried by the driver.

## Enforced boundary

- Explicit --embedded-profile=scalar-v0 with one input and distinct --header/-o
  outputs. CLI option allowlist precedes early-return actions, rejecting verbs,
  standalone/JIT, codegen/checking overrides, all -D, imports/native includes and
  runtime generation commands. GS_DEBUG=1 is forced in profile C.
- Root sidecars rejected before interpretation; parser rejects import/namespace/
  extern directives before package resolution or fetching, including empty
  extern blocks. Ast's default-off policy preserves ParseProgram's signature.
- Parsed source walker visits all declarations/bodies, including unused/dead
  code: only scalar function/AST/type/operator forms in SCALAR_PROFILE.md.
  Direct call graph must be acyclic; all named callees must be admitted functions.
- Checked-specialization walker runs before Optimizer: actual storage/expression
  types, calls, parameters/returns and cycle state must satisfy the subset.
  Representable adaptable literals are distinguished from runtime i64 values.
- After existing codegen accounting, require zero main/global regions, no worker
  entries, queues, foreign/dynamic calls, nonlocal-return channels, pools, user
  global storage or embedded shader state. Fail closed on unsupported source
  nodes and unsupported resolved calls.
- C/header staged after checks, then renamed individually. Source validation
  failure leaves existing outputs unchanged; staging failure cleans temporary
  files; publication failure invalidates the header. Paths aliasing source or
  each other and existing/aliased staging paths are rejected. This is not a
  two-file transaction; consumers must honor exit status and serialize writers.

GS_SCALAR_V0_VALIDATED=1 identifies validator revision 1. It does **not** select
an allocation-free runtime or prove target ABI compatibility. Emitted C still
requires the unmodified desktop runtime. The design's restricted lifecycle and
platform panic boundary are the next separate change.

## Verification

Commands executed:

```sh
cmake -S .cache/goose-scalar -B build/goose-scalar -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/goose-scalar -j 2
python3 tools/test_scalar_validator.py --compiler build/goose-scalar/goose
```

Build: PASS, with previously recorded upstream warnings (unused items and GCC
maybe-uninitialized in Roots/small_vector). No new validator warning observed.
This development checkout retains the upstream pin's normal version string;
reproduction instructions set an explicit validator GOOSE_VERSION identifier.

Final runner: **237 commands matched expected status; 209 expected exit-1
cases, 28 exit-0 commands**. One exit-0 command invokes the existing **19-command
host probe**, which also passes. [Archived summary](scalar-validator-results.json)
records the patch digest, source cases, levels and counts; detailed local command/
stdout/stderr records are in build/scalar-validator-tests/results.json. The test
suite is [test_scalar_validator.py](../tools/test_scalar_validator.py).

Coverage at Goose/native C -O0 and -O2:

- Accepted arithmetic, boolean locals/control, direct calls, assignments, unused
  scalar helper, INT32_MIN literal, typecheck-folded literal arithmetic and
  library restart compute expected results with desktop runtime.
- Addition/subtraction/multiplication/negation overflow exit 1, proving the forced
  arithmetic checking remains active at both optimization levels.
- 46 source rejection cases plus a malformed sidecar, including unsupported
  types, references/aggregates, globals, generics/modifiers, recursion, foreign
  calls, loops, strings, casts, nested functions, dead/uncalled I/O, and inferred
  i64 locals inside a dead branch. JSON diagnostics retain profile information.
- Nineteen conflicting-option forms before/after the opt-in flag, eight verb
  forms, unknown profile names, missing outputs, source/output symlinks/aliases,
  failed staging, stale output preservation and temporary-file cleanup.
- Profile-looking words passed as program arguments or option operands do not
  opt a desktop command into validation.
- Fresh archive+patch/file-digest reproduction, refusal of existing destinations
  and wrong upstream pin. Seven normal desktop source fixtures still emit C
  without opt-in at both levels; original host probe additionally runs normal
  check/emission/native C/library/layout tests.

Scoped upstream tests also PASS: check_cli_paths(exe, None, base) and
check_diagnostics_json(exe, base) from the pinned source. C-build branches in
check_cli_paths are deliberately skipped by its None toolchain parameter;
native builds are covered by the project probes. Reproduce these scoped tests
with the standard library installed beside the binary (the CLI path test
intentionally strips GOOSE_STDLIB):

```sh
# Local build layout used here; create only if the stdlib link is absent.
ln -s ../../.cache/goose-scalar/stdlib build/goose-scalar/stdlib
python3 - <<'PY'
import os, sys
from pathlib import Path
root = Path.cwd()
src = root / '.cache/goose'
sys.path[:0] = [str(src / 'test'), str(src / 'scripts')]
os.environ['GOOSE_HOME'] = str(root / 'build/upstream-validator-regressions/home')
os.environ['GOOSE_STDLIB'] = str(src / 'stdlib')
from cli_paths import check_cli_paths
from diagnostics_json import check_diagnostics_json
exe = str(root / 'build/goose-scalar/goose')
base = root / 'build/upstream-validator-regressions'
check_cli_paths(exe, None, base)
check_diagnostics_json(exe, base)
print('PASS: scoped upstream frontend regressions')
PY
```

Full upstream compiler/LSP/sanitizer suites were not run. Runtime initialization
remains desktop behavior, so these tests establish neither allocation-free
execution nor MCU memory/stack budgets. No target ABI, interrupts or concurrency
support is claimed.

## Corrective findings during implementation

- An initial ParseProgram parameter addition conflicted with its LSP declaration;
  replaced with a default-off Ast policy without changing the function API.
- An initial negative literal-arithmetic fixture actually passed because Goose
  typechecking folds 1 + 2 to an admitted result. Converted it to a positive
  semantic test; unsupported source constructs are still checked before that
  transformation.
- A draft higher-order fixture used incorrect syntax; corrected using upstream
  trailing-block syntax. Final source fixtures fail with profile diagnostics,
  not accidental parse errors.
- Git's ceiling must be the destination's parent to prevent discovery of this
  enclosing repository. Initial preparation skipped patches despite exit 0;
  corrected the ceiling and added reviewed per-file hash checks plus reproduction
  tests. No source outside the disposable destination was modified.
- Scoped upstream tests initially lacked their Python helper search path and
  then their expected stdlib layout; supplied scripts/ imports and installed a
  local stdlib symlink. These were harness/environment failures, not compiler
  behavior regressions. Final scoped runs pass.

Final CLI review also corrected opt-in detection to stop at -- and skip option
operands. Regression tests prove profile-looking program arguments/stdlib
operands preserve normal run/check behavior; both scoped upstream suites were
rerun after that correction and passed.

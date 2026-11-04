# Host feasibility probes

Requires Git, CMake >=3.27, Ninja, C++20 compiler, C compiler, Python 3.
No ESP-IDF, downloads, flashing, or target execution occurs in the probe.
From the repository root (network needed for setup):

```sh
mkdir -p .cache
git clone https://github.com/aardappel/goose.git .cache/goose
git -C .cache/goose checkout --detach 335fddc13dc74666398ffe160ec8a8f2958329d0
cmake -S .cache/goose -B build/goose -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/goose -j 2
python3 tools/host_probe.py --compiler build/goose/goose
```

If .cache/goose exists, verify its revision/cleanliness instead of cloning again.
`--source` and `--compiler` accept existing paths; the initial session built in
/tmp/goose-build from /tmp/goose-upstream at the same pinned revision.
The probe runs check/emission/native C execution for scalar and growing data,
C hosts that initialize/call/exit twice (with main and a zero-region leaf library),
and a freestanding GCC-compatible
`-m32` layout witness. The last probe needs x86 compiler support but no 32-bit
libc; it is not Xtensa verification. `--cc` names a single compiler executable.
Failure is fatal and preserves the command/stdout/stderr in
build/host-probe/results.json. The compiler path must be built from the clean
pinned source; the source check cannot prove binary provenance.

Generated C and compiler output remain ignored; copy a concise results summary
into research/EXPERIMENTS.md after reviewing it. Do not infer target compatibility
or allocation-free execution from these host probes.

## Separate-runtime dependency probe

```sh
python3 tools/runtime_probe.py --compiler build/goose/goose
```

This additional probe requires Linux, a GCC-compatible compiler, GNU nm and a
GNU-compatible linker supporting --wrap and --gc-sections. It does not modify
upstream sources. At Goose/native C -O0 and -O2 it emits a separate runtime,
records undefined symbols, and links the leaf library to an observer. It checks
lifecycle/restart/idempotence and expects runtime failures before init, after
exit and on checked i32 overflow. It also compiles counterexamples showing why
zero regions and GS_MAX_STACKS=0 do not enforce the proposed profile. These
counterexamples are accepted upstream, not passed target-profile rejection tests.

Output: build/runtime-probe/{results,summary}.json; a successful run currently
executes 32 commands (six deliberate exit-1 cases). The observer counts direct
linker-wrapped calls to selected APIs, not allocations internal to shared libc.
See research/RUNTIME_STARTUP.md for semantics/limitations and
research/runtime-{results,summary}.json for the reviewed session evidence.
No embedded runtime or scalar-v0 enforcement is implemented by this script.

## Scalar-v0 validator compiler (desktop runtime)

Use a fresh destination; preparation intentionally refuses to overwrite one:

```sh
python3 tools/prepare_scalar_compiler.py
cmake -S .cache/goose-scalar -B build/goose-scalar -G Ninja -DCMAKE_BUILD_TYPE=Release -DGOOSE_VERSION=335fddc+scalar-v0-validator
cmake --build build/goose-scalar -j 2
python3 tools/test_scalar_validator.py --compiler build/goose-scalar/goose
```

`--upstream` selects an existing clean checkout at the project pin; no helper
fetches sources. See patches/goose/README.md for patch provenance and maintenance.
If .cache/goose-scalar already exists, inspect it and choose another
`--destination`; use that path in CMake and `--source` in the test runner.
The initial development build used the pin's normal version string; the explicit
GOOSE_VERSION above helps distinguish future validator binaries.

Example validation and C emission (not a target build):

```sh
build/goose-scalar/goose --embedded-profile=scalar-v0 --header build/leaf.h -o build/leaf.c examples/leaf.goose
```

Only explicit library C emission is accepted. GS_DEBUG=1 is forced; all user
-D options and run/build/check/fetch/standalone/JIT modes are rejected, as are
imports, sidecars and user headers. Read docs/SCALAR_PROFILE.md for the subset.
The C marker GS_SCALAR_V0_VALIDATED=1 means validator revision 1, not a target
runtime ABI. Output still needs the desktop runtime from --emit-runtime.

The test runner checks accepted computation and checked overflow, source/flag
rejections at both levels, existing/fresh output handling, aliases/staging
failures, reproducible patch application and wrong-pin/existing-destination
refusal. It also runs the earlier 19-command desktop host probe on the patched
compiler. Logs live in build/scalar-validator-tests/results.json; archived
summary and test scope are in research/SCALAR_VALIDATOR.md.

Upstream CLI path tests deliberately strip GOOSE_STDLIB; when building outside
the upstream tree, install/copy (or locally symlink) its stdlib beside the
compiler before invoking those upstream tests. The project probes explicitly
set GOOSE_STDLIB and do not require that layout.

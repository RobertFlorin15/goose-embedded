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
python3 tools/prepare_scalar_compiler.py --validator-only
cmake -S .cache/goose-scalar -B build/goose-scalar -G Ninja -DCMAKE_BUILD_TYPE=Release -DGOOSE_VERSION=335fddc+scalar-v0-validator
cmake --build build/goose-scalar -j 2
python3 tools/test_scalar_validator.py --validator-only --compiler build/goose-scalar/goose
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

For the historical validator-only compiler, only explicit library C emission is accepted. GS_DEBUG=1 is forced; all user
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

## Scalar runtime ABI 1

Current default preparation applies both tracked patches. Use a fresh destination:

```sh
python3 tools/prepare_scalar_compiler.py --destination .cache/goose-scalar-runtime
cmake -S .cache/goose-scalar-runtime -B build/goose-scalar-runtime -G Ninja -DCMAKE_BUILD_TYPE=Release -DGOOSE_VERSION=335fddc+scalar-v0-runtime
cmake --build build/goose-scalar-runtime -j 2
python3 tools/test_scalar_runtime.py --compiler build/goose-scalar-runtime/goose
python3 tools/test_scalar_validator.py --compiler build/goose-scalar-runtime/goose
```

For historical validator-only behavior use --validator-only in preparation and
in test_scalar_validator.py, with the matching source tree/binary. The older
validator instructions above require that flag now. Both modes keep .cache/goose
clean. Current profile output embeds a small C11 runtime; it does not link the
desktop --emit-runtime object. The C host must implement the generated header's
non-returning ge_scalar_v0_panic_v1(message, file, line) prototype. No ready-made
ESP-IDF binding is implemented. tests/scalar_v0/panic_host.c is Linux host test
code using write/_Exit, not a firmware platform adapter.

The runtime probe needs GCC, Clang's i386 backend, GNU nm and a GNU --wrap-capable
linker. It inspects native objects without LTO or section garbage collection,
compiles generic 32-bit freestanding objects (not Xtensa), observes selected heap/
VM/signal/pthread calls, tests lifecycle and panic guards, tests missing/wrong
panic ABI linkage and checked arithmetic against Python integer results.
The clean host link uses no -lm/-pthread or desktop runtime object; its separate
observed version includes the host-only observer. Host startup/libc internals
are outside the claim about profile-generated code.

If modifying a canonical runtime file, regenerate and rebuild before probing:

```sh
GOOSE_RUNTIME="$PWD/.cache/goose-scalar-runtime/src/runtime" build/goose-scalar-runtime/goose --gen-runtime-header
cmake --build build/goose-scalar-runtime -j 2
```

The committed second patch already includes regenerated runtime text, so a fresh
preparation needs one build. The initial development bootstrap needed a build,
regeneration and rebuild. See research/SCALAR_RUNTIME.md for verified outcomes.

## Pinned ESP-IDF baseline (no hardware access)

Linux x86_64 setup used for the initial experiment: Git, Python 3.14.4 with venv,
CMake 4.2.3 and Ninja 1.13.2. ESP-IDF requires Python >=3.10; other host versions
are not yet verified by this project. Downloads need network access and several
GB of disk space. Keep all caches inside the project:

```sh
git clone --branch v6.0.2 --depth 1 --recursive --shallow-submodules https://github.com/espressif/esp-idf.git .cache/esp-idf-v6.0.2
git -C .cache/esp-idf-v6.0.2 rev-parse HEAD
mkdir -p build/esp-idf-setup
IDF_TOOLS_PATH="$PWD/.cache/espressif" PIP_CACHE_DIR="$PWD/.cache/pip" PIP_CONSTRAINT="$PWD/tools/esp-idf-python.lock" bash .cache/esp-idf-v6.0.2/install.sh esp32s3 > build/esp-idf-setup/install.log 2>&1
python3 tools/esp_idf_baseline.py
```

Expected SDK commit: 7101770dc6db2667b3c477cc31365dd1acd6db4e. Do not reclone over
an existing checkout; verify its commit/status/submodules first.
esp-idf-python.lock records the Python 3.14/Linux
environment verified here, including transitive packages, pip and setuptools.
PIP_CONSTRAINT applies those exact versions during setup; the helper rejects
installed-package drift. Upstream constraints are still honored. If they later
conflict with this lock, review and checkpoint an explicit upgrade; do not bypass
the checks. Package/archive availability and other hosts remain external limits;
this is not a hermetic or bit-for-bit build promise. The original installation
resolved upstream constraints first and generated the lock; a replay with the
lock is recorded separately in the report.

Installation is separate from the build helper, which does not install tools or
fetch SDK sources. It
activates upstream export.sh in a child shell, checks the source/tool pin, copies
hello_world unchanged, configures esp32s3 with idf.py set-target, then builds via
`cmake --build ... --parallel 2`. CMake's build interface bounds parallelism;
idf.py v6.0.2 has no -j option. No menuconfig changes are applied.

Output defaults to build/esp-idf-baseline/{hello_world,firmware,results.json,*.log}.
It must not exist; use --output build/esp-idf-baseline-2 for a fresh run. Failed
commands retain logs and failed status. The helper verifies original file hashes,
target identity, artifact presence and Xtensa ELF header, records versions,
installed Python packages, constraints digest, map and size, and rechecks SDK
cleanliness. It prevents enclosing project Git discovery from supplying a
changing application version. See [the report](../research/ESP_IDF_BASELINE.md)
for results and evidence limits. No command opens a device, flashes or monitors.

## ESP32-S3 scalar leaf component

After the compiler/runtime and official SDK baseline gates, run:

```sh
python3 tools/test_esp_idf_scalar.py --output build/esp-idf-scalar-new
```

Requires the prepared .cache/goose-scalar-runtime source and
build/goose-scalar-runtime/goose, clean SDK and tools from the preceding sections,
Linux host cc and the exact Python package lock. The helper verifies source
digests/version and records the compiler binary hash; it cannot prove that an
arbitrary binary was built from those sources. No download or hardware operation.
Output must be fresh; --compiler/--sdk/--tools/--jobs may select existing paths.

The tracked examples/esp32s3_scalar project generates leaf C/header through the
host compiler, builds the scalar/platform/main components at -O0 and -O2 without
LTO, records target object/final symbols and assembly plus stack-usage reports,
and compiles an arithmetic fixture as target C11. It verifies panic configuration
and C ABI assertions and runs Linux tests of the real panic adapter with a
terminating SDK double, including ABI/panic-policy compile refusals. Logs and
full results remain under the chosen output. research/ESP32S3_SCALAR.md records
the historical 53-command integration gate. The stack-observation checkpoint passed 73
commands (18 expected failures); research/STACK_MEASUREMENT.md and its reviewed
JSON record the audit, host application sequencing tests and simulated wider
stack-element rejection. Target-only ABI checks remain compiled. The example
records four lifetime byte low-water readings, with the post-report sample
debugger-only. No actual target readings exist yet. Supplementary ROM revision-0
inspection does not establish the user's silicon revision.
Physical execution, whole-task stack budget and per-board settings are separate
gates; read docs/HARDWARE_VALIDATION.md. No claim that one image fits all modules.

## Configuration overlays and offline saved logs

Append reviewed ESP-IDF defaults with repeated --defaults, supplying --config-id:

```sh
python3 tools/test_esp_idf_scalar.py --config-id my-config --defaults /path/to/reviewed.defaults --output build/my-config
python3 -m unittest discover -s tests -p test_scalar_tools.py -v
```

The base policy comes first. Input bytes and optional .esp32s3 siblings are
snapshotted/hashed; each level has its own effective sdkconfig. Unknown Kconfig
symbols and incompatible effective target/panic/LTO settings fail before build;
existing C guards remain. Paths with CMake list/newline delimiters are rejected.
After all probe checks pass, O0/run-manifest.json and O2/run-manifest.json record
artifact/config hashes and configuration identity. Current probes pass 75 commands
per configuration (18 expected failures); build-only control and 4 MB/4096-byte
overlay fixtures both pass. These are not verified board definitions.

The example prints full ELF identity and a completion marker around existing
result/stack telemetry. To check an independently saved capture JSON and raw log:

```sh
python3 tools/validate_scalar_run.py --manifest build/my-config/O0/run-manifest.json --capture /path/to/capture.json
```

Exit 0 means supplied files are consistent; it never authenticates hardware
execution or stack safety. All current automated captures are synthetic. The
28 unittest cases need no SDK/hardware and cover mismatches, malformed/partial
records, failed boots/panics, tampering and path boundaries. See
[RUN_LOG_FORMAT.md](../docs/RUN_LOG_FORMAT.md) for schema/layout and
[the verified report](../research/CONFIGURATION_LOG_VALIDATION.md) for evidence.

### Selectable fatal firmware (build/test only)

```sh
python3 tools/test_esp_idf_scalar.py --case cold-export --output build/cold-new
python3 tools/test_esp_idf_scalar.py --case overflow --output build/overflow-new
python3 -m unittest discover -s tests -p 'test_scalar*.py' -v
python3 tools/validate_scalar_fatal.py --manifest build/overflow-new/O0/run-manifest.json --capture /path/to/capture.json
```

Default case is success. Keep each case/configuration in a fresh output; manifests
and fatal captures explicitly identify case. Normal/fatal validators reject each
other's build cases. See [fatal protocol](../docs/FATAL_RUN_LOG_FORMAT.md) for exact
expected messages, host-double limits and source evidence. No command here opens
a device or authorizes hardware operations. Offline consistency never proves
execution, physical halt or a stack bound.

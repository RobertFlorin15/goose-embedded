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

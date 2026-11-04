# Experiments — 2026-11-04

Evidence level: Linux x86-64 host execution and source inspection only.

## Environment

Git 2.53.0; GCC 15.2.0; CMake 4.2.3; Ninja 1.13.2; Python 3.14.4.
Official Goose clean revision 335fddc13dc74666398ffe160ec8a8f2958329d0.
Binary reports `goose 335fddc (runtime d22ae129d92b)`.
`idf.py` and `xtensa-esp32s3-elf-gcc` were not in PATH. No target
installation or connected board was identified; absence from PATH is not a
complete filesystem inventory of SDK installations.

## Build

```sh
git clone --depth 1 https://github.com/aardappel/goose.git /tmp/goose-upstream
cmake -S /tmp/goose-upstream -B /tmp/goose-build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/goose-build -j 2
python3 tools/host_probe.py --compiler /tmp/goose-build/goose
python3 /home/robert/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/goose-embedded
```

Clone required network-enabled execution because sandbox DNS failed. Retry
changed execution environment; no source modification was needed. A clean copy
at the same pin remains in .cache/goose for durable local reuse; ignored caches
are disposable. Build completed 23/23 steps, exit 0. Upstream emitted warnings:
`gs_end` noreturn return, unused functions/variable/parameter, and a GCC
maybe-uninitialized report involving Roots/small_vector. They are unresolved
upstream warnings, not proven defects; full upstream tests/sanitizers were not run.

## Results

Host probe: **19 commands passed**, all exit 0. Raw commands, output and stderr
are checked in as [host-results.json](host-results.json); absolute paths describe
this run and can be overridden/recreated per tools/README.md.

| Experiment | Observable result | Limit |
|---|---|---|
| scalar check, C emission, C11 GCC build/run | `goose-embedded: 42`; 1 region | Print/assert workload, not a zero-stack program |
| growable u8 array, 32 elements | `growth: 32`; 2 regions | Desktop virtual memory runtime |
| exported scalar from C host, two init/exit cycles | Expected 42 both times; two Goose main outputs | Host ABI and lifecycle only |
| leaf scalar export, no main, two init/exit cycles | Expected 42; zero regions in report | Still enters desktop gs_rt_init |
| freestanding -m32 packed layout witness | Static assertions compiled | 32-bit x86 C layouts, not Xtensa execution |
| project skill validation | `Skill is valid!` | Syntax validation, not behavior proof |

No target compilation, simulator, hardware, overflow-on-target, ISR, or HAL test
was executed. No target memory footprint is known. These probes are smoke tests
of this project's feasibility assumptions, not a claim that upstream's complete
compiler suite passes.

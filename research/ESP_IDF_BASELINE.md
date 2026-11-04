# ESP32-S3 SDK baseline

2026-11-05. Scope: build the **unchanged official** hello_world before adding
Goose. This is a target compilation experiment, never a hardware execution test.
**PASS:** official ESP32-S3 ELF and flash images linked. No Goose target build or
hardware execution occurred. Reviewed evidence:
[esp-idf-baseline-results.json](esp-idf-baseline-results.json).

## Selected SDK and toolchain

Use ESP-IDF v6.0.2, commit
`7101770dc6db2667b3c477cc31365dd1acd6db4e`, annotated tag object
`b0d7ee8723d5cd90c1aa2c54729aa7c92f2bf187`.
The [official release](https://github.com/espressif/esp-idf/releases/tag/v6.0.2)
identifies this as a v6.0 bugfix release; its
[ESP32-S3 guide](https://docs.espressif.com/projects/esp-idf/en/v6.0.2/esp32s3/get-started/index.html)
labels v6.0.2 stable. This is a concrete starting pin, not a policy of following
the latest release automatically.

The pinned
[tools manifest](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/tools/tools.json)
selects Xtensa GCC 15.2.0, distribution `esp-15.2.0_20251204`, and contains
platform archive SHA-256 values checked by the official installer. The project
pin in [esp-idf-pin.json](../tools/esp-idf-pin.json) checks the entire manifest's
digest and records the Linux amd64 Xtensa archive digest. SDK gitlinks pin the
submodules; the baseline helper refuses missing/mismatched/dirty submodules.

Use the still-supported
[legacy installer](https://docs.espressif.com/projects/esp-idf/en/v6.0.2/esp32s3/get-started/linux-macos-setup-legacy.html)
to install in project-local .cache/espressif. EIM is the default documented
installer for v6, but would add another tool/configuration dependency for this
single SDK experiment. No system package installation or shell profile change.
install.sh esp32s3 also installs auxiliary RISC-V/ULP/debug tools selected by
Espressif; these downloads do not expand Goose's supported target scope.

Python package constraints are downloaded separately from the SDK revision and
can refresh daily (pinned tools/idf_tools.py:get_constraints). Record their hash
and `pip freeze --all` alongside build evidence; an SDK commit alone is not a
complete Python environment pin. Setup instructions are in
[tools/README.md](../tools/README.md).

## Verified experiment

Host: Ubuntu 26.04 Linux x86_64, Python 3.14.4, CMake 4.2.3, Ninja 1.13.2.
Neither idf.py nor an ESP32-S3 GCC was initially on PATH; ~/esp and ~/.espressif
were absent. Network access required the execution environment's network
approval; all downloads went to ignored project caches. No system packages,
shell profiles or hardware were changed. The host lacks flex, bison and ccache
on PATH; this particular minimal build succeeded without them. That does not
remove the official prerequisites for arbitrary SDK projects.

Commands (working directory: repository root):

```sh
git clone --branch v6.0.2 --depth 1 --recursive --shallow-submodules https://github.com/espressif/esp-idf.git .cache/esp-idf-v6.0.2
IDF_TOOLS_PATH="$PWD/.cache/espressif" PIP_CACHE_DIR="$PWD/.cache/pip" bash .cache/esp-idf-v6.0.2/install.sh esp32s3 > build/esp-idf-setup/install.log 2>&1
python3 tools/esp_idf_baseline.py
IDF_TOOLS_PATH="$PWD/.cache/espressif" PIP_CACHE_DIR="$PWD/.cache/pip" PIP_CONSTRAINT="$PWD/tools/esp-idf-python.lock" bash .cache/esp-idf-v6.0.2/install.sh esp32s3 > build/esp-idf-setup/locked-replay.log 2>&1
```

- Initial install and locked replay against the existing installation: exit 0.
  The replay verifies constraint compatibility, not a second fresh installation.
  All six official downloaded tool archives independently matched pinned hashes.
- The SDK and 25 recursive submodules match their pins and remain clean.
- The 58 installed Python packages (including pip/setuptools) exactly match
  tools/esp-idf-python.lock. The build helper enforces that lock. The live
  espidf.constraints.v6.0.txt digest is recorded in the results.
- The helper's five commands passed: package inventory, set-target, CMake build
  (543 top-level Ninja steps plus bootloader sub-build), readelf, idf.py size.
  Activation also succeeded. Build/configuration logs contain no compiler or
  CMake warnings/errors detected by the reviewed text search.
- All six original example files retain their SHA-256 values. No menuconfig
  settings were edited. Generated sdkconfig and its hash are recorded. Defaults
  include DIO/2 MB flash, single-app partition, 100 Hz RTOS tick and a 3584-byte
  main task stack. These are build settings, not verified board properties or a
  measured stack budget. Application version is 1; SDK reports v6.0.2. The
  helper prevents discovery of the enclosing Goose Embedded Git repository.
- ELF header: ELF32, little endian, Tensilica Xtensa, executable. Linked artifacts:

| Artifact | Bytes |
|---|---:|
| hello_world.elf (includes debug information) | 3,164,440 |
| hello_world.bin | 145,424 |
| bootloader.bin | 21,056 |
| partition-table.bin | 3,072 |

The map and compile commands remain in build/esp-idf-baseline/firmware; reviewed
artifact/config/source/log hashes and the ELF header are tracked in the result
summary. The size tool reports 145,313 bytes before image padding. The application
fits the default 1 MiB app partition with 86% free. These are baseline firmware
figures, not Goose overhead measurements.

Five helper refusals passed: existing output, non-positive jobs, wrong SDK
revision, spaces in paths, and output overlapping the SDK. Existing outputs are
never overwritten. Python syntax and Git whitespace checks pass. The installer
replay did not change the package lock. Goose compiler/runtime code was unchanged,
so their historical host suites were not rerun for this SDK-only checkpoint.

Next: compile the validated scalar leaf as a separate ESP-IDF component with a
small app_main and required non-returning panic binding; inspect the resulting
Xtensa symbols, assembly, map and native stack use. Hardware remains a later gate.

## Acceptance criteria

- SDK at the pin, all submodules initialized at gitlinks, clean before/after.
- Official tool installer succeeds and project-local target GCC version matches.
- Original hello_world files retain their hashes after configuration/build.
- Configure for esp32s3; link ELF, application/bootloader/partition images and map.
- ELF header identifies 32-bit little-endian Xtensa; retain size/config/tool data.
- Logs/results preserve failure status and do not imply execution.

## License and evidence limits

The SDK root is Apache-2.0; hello_world_main.c carries CC0-1.0. Component and
toolchain licenses differ (tools.json lists GPL variants for compiler/debugger).
The downloaded SDK, example copy, binaries and toolchain remain ignored; this
change does not redistribute their code. A future binary release still needs
the full selected-component license inventory. No project license chosen here.

This baseline contains no Goose, profile runtime, panic adapter or HAL. Successful
linking alone will not establish a native stack budget, panic safety or correct
physical execution of Goose code.

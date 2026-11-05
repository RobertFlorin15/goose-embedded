# Configuration snapshots and offline telemetry consistency

2026-11-05. Starting checkpoint 04b4b5aed7615ff3ea95d3eb5a28ba769cb34417.
**Four target firmware builds and synthetic saved-file tests pass. Zero physical
runs, simulator executions, serial captures or hardware operations.** M2b remains
unverified and no HAL work was started.

## Changes

- Added ordered --defaults overlays and explicit configuration IDs to the scalar
  probe. Base policy remains first; snapshot each input and optional .esp32s3
  sibling, record hashes, reject mutation, and check actual target/panic/LTO policy
  before compiling. Unknown Kconfig symbols fail. Symlink lookup preserves SDK
  pathname semantics while snapshots copy bytes rather than links.
- Each successful level publishes run-manifest.json for local effective config,
  SDK/compiler identity and ELF/app/boot/partition hashes. No network or device
  access is involved. Referenced external files remain a reproducibility boundary.
- app_main prints the full ELF descriptor hash using fixed static storage, then
  existing computation/stack telemetry, then a completion marker after the fourth
  sample. SDK default short hashes would be insufficient for exact matching.
- Added tools/validate_scalar_run.py: reads manifest/capture/log/artifacts and
  reports consistency or rejection. It never certifies hardware execution or a
  complete stack bound, even if the capture declares physical evidence.
- Protocol and JSON contract: [RUN_LOG_FORMAT.md](../docs/RUN_LOG_FORMAT.md).

Source evidence at SDK 7101770dc6db2667b3c477cc31365dd1acd6db4e:
[project.cmake defaults handling](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/tools/cmake/project.cmake#L673),
[target-specific defaults](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/tools/cmake/kconfig.cmake#L173),
[public image descriptor](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_app_format/include/esp_app_desc.h#L35).
Installed esptool 5.6.0's cmds.py/bin_image.py were inspected: image generation
inserts the ELF digest, and image-info reports the descriptor's full hash. The
probe verifies that value against the actual linked ELF; no ROM/board inference.

## Reproduction and results

Pinned compiler, SDK, toolchain and Python lock unchanged. Follow tools/README.md.

```sh
python3 -m unittest discover -s tests -p test_scalar_tools.py -v
mkdir -p build/config-fixtures
cp tests/esp_idf/configs/four-mb.defaults build/config-fixtures/four-mb.defaults
cp tests/esp_idf/configs/four-mb.defaults.esp32s3 build/config-fixtures/four-mb.defaults.esp32s3
python3 tools/test_esp_idf_scalar.py --output build/esp-idf-config-control
python3 tools/test_esp_idf_scalar.py --config-id test-4mb --defaults build/config-fixtures/four-mb.defaults --output build/esp-idf-config-overlay
```

The ignored build-only overlay fixture contains
CONFIG_ESPTOOLPY_FLASHSIZE_4MB=y; its .esp32s3 sibling contains
CONFIG_ESP_MAIN_TASK_STACK_SIZE=4096. These are test settings, not a definition
for any user board. The control uses effective 2 MB/DIO and 3584-byte main stack.
Both remain chip target esp32s3 with no enabled PSRAM and the minimal panic policy.

| Configuration | Target levels | Probe commands | Expected failures | App image bytes -O0/-O2 |
|---|---|---:|---:|---|
| control | -O0/-O2 | 75 | 18 | 146144 / 145824 |
| test-4mb | -O0/-O2 | 75 | 18 | 146144 / 145824 |

Each firmware has 548 top-level Ninja steps plus bootloader. App frame remains
48 bytes at both levels; new hash conversion uses static storage. Bootloaders
and partition images/config hashes are recorded in the results. Same image size
does not mean identical firmware; hashes/config identities differ. No whole-task
stack guarantee follows. The first sample now also includes identity printing;
the final completion print remains outside all four samples.

All prior profile-object/adapter imports, ABI witnesses, target arithmetic compilation/host leaf computation,
panic-policy guards and actual application host-double sequencing tests pass.
Mixed-byte descriptor fixtures check all 64 hash digits, initialization/reset,
identity-before-sampling and completion-after-final-sample order. Five existing
generated unused-helper/metadata warnings per level remain, no new app warning
or suppression. Compiler/runtime patches and platform panic binding unchanged.

28 host unittest cases pass (with additional table-driven subcases): snapshots,
ordering/target siblings/symlinks/mutation, effective policy, correct and wrong
configuration/firmware identity, artifact/log hash tampering, path escapes,
duplicate keys, complete/partial/duplicate/malformed/out-of-order telemetry,
known fatal/reset output, scalar result, sample range/units/order, zero readings,
partial or inconsistent debugger records and CLI exit behavior. All values and
captures in these tests are synthetic, including tests declaring physical type
to confirm that the validator does not authenticate it.

Six supplementary strict application-host compile/run checks pass at the final
test-source revision, covering success and wrong-result termination at both levels.
Four additional synthetic CLI captures validate against the four actual local
build manifests; selecting the wrong manifest is rejected. Captures start with
SYNTHETIC TEST DATA and declare evidence_type=synthetic; none came from a board.
Two target configuration refusal experiments fail after configuration but before
firmware compilation: enabled debugger-aware panic and an unknown Kconfig symbol.
Both retain failed status and publish no run manifest. SDK/reference Goose trees
remain clean. Python syntax, source/artifact/log integrity, local Markdown and
Git whitespace are checked at the final checkpoint.

Reviewed result summary: [configuration-log-results.json](configuration-log-results.json).
Raw per-build results/configs/manifests/images/logs remain in ignored
build/esp-idf-config-{control,overlay,bad-policy,unknown}; unit/synthetic logs
in build/config-fixtures. Root-level snapshots are preserved for repeatability,
not a hermetic or bit-identical build promise. Historical stack audit remains
in [STACK_MEASUREMENT.md](STACK_MEASUREMENT.md).

## Limits / next gate

File consistency can be forged; record hashes are integrity checks, not signatures
or proof of execution. Firmware output alone cannot identify the carrier/module,
flash/PSRAM hardware, authorize operations or prove a stack bound. Debugger-only
after_report is not present numerically in serial; completion is only a progress
marker. Unknown failures and later events may be absent from a supplied capture.
No board preset, full language port, interrupt/concurrency feature or HAL added.

Next: prepare separately selectable fatal-case firmware and its offline expected
diagnostic checks, while retaining per-configuration manifests and explicit
hardware authorization gates. An actual identified configuration and physical
logs are still needed for M2b; the user's multiple-board goal remains unchanged.

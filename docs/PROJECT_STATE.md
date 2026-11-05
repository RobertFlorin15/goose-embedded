# Project state

Updated 2026-11-05. Reconcile with Git/source. Current evidence:
[CONFIGURATION_LOG_VALIDATION.md](../research/CONFIGURATION_LOG_VALIDATION.md),
[configuration-log-results.json](../research/configuration-log-results.json).
Historical stack, scalar integration and compiler/runtime reports remain in research/.

## Current milestone and task

M1 analysis and M2a scalar leaf cross-build/ABI gate complete. Current task:
**explicit configuration inputs, run manifests and offline normal-log consistency
checks verified**. M2b physical execution remains unverified. No actual serial
capture, hardware readings, simulator run, full task stack bound or HAL exists.
Next: separately selectable fatal-case firmware and offline expected-diagnostic
checks, preserving per-configuration identities and physical-operation gates.

## Completed tasks

- Durable agent instructions/skill, roadmap, architecture/decisions/learning and
  checkpoints established. Grapify unavailable in prior checks; standard tools.
- Goose 335fddc13dc74666398ffe160ec8a8f2958329d0 with tracked scalar validator/runtime
  patches 0001/0002 remains unchanged. Versioned SDK panic binding unchanged.
- ESP-IDF v6.0.2 / 7101770dc6db2667b3c477cc31365dd1acd6db4e, 25 recursive submodules,
  Xtensa GCC 15.2.0 (esp-15.2.0_20251204), tools/Python lock remain pinned.
- Prior scalar leaf/ABI/dependency checks and four normal-task low-water samples
  remain enabled. Target-only pointer/prototype witness compiles in both levels.
- Probe accepts ordered --defaults overlays with explicit --config-id; base policy
  first. Snapshots original bytes and optional .esp32s3 siblings, including lookup
  beside a supplied symlink. Hashes detect source/snapshot mutation. Effective
  target/panic/LTO and unknown-symbol checks fail before firmware compilation.
- Successful levels publish run-manifest.json: configuration/SDK/compiler identity,
  effective sdkconfig and ELF/app/boot/partition hashes, main-stack setting.
- app_main prints the full SDK descriptor ELF hash in fixed static storage before
  sampling, and a completion marker after completed=4. esptool image-info matches
  each image's embedded digest to its actual ELF. Host doubles test full 64-digit
  conversion and ordering. No compiler/runtime/Goose API or panic behavior changes.
- Offline validator checks local artifacts, record/log hashes, configuration,
  level/identity, ordered normal telemetry, known fault/reset cues and sample
  shape/range. Hashing/parsing use the same byte snapshots; logs bounded to 16 MiB.
- Protocol/record schema in docs/RUN_LOG_FORMAT.md; per-board run template updated.
  User wants future coverage across several board types; no guessed board presets.

## Findings / limitations

- A result-42 line alone is insufficient to correlate firmware. Full ELF identity
  plus a manifest detects accidental mismatches; it does not authenticate edited
  logs, independently attest all config bits, identify a module or authorize actions.
- Offline success is only status=consistent; hardware_execution_proven and
  stack_bound_proven always false. Current automated captures declare synthetic.
  Missing debugger sample stays null; numeric fourth reading is not in serial.
- Zero is valid reported data and flagged, never certified safe. Missing/duplicate/
  malformed/out-of-order telemetry, partial debugger records, known fatal/reset
  lines and hash/path mismatches are rejected. Unknown/later failures can be absent
  from a capture. No parser proves real hardware execution or a full stack bound.
- Identity output precedes first low-water sample and can affect every reading.
  Final completion printing and SDK return/task deletion are outside all four
  samples. Current app frame remains 48 bytes. Earlier SDK/ROM audit frame sums
  remain partial; ROM callbacks/revision, window/exception/interrupt costs unresolved.
- Control effective config is DIO/2 MB, main stack 3584. Build-only test-4mb uses
  flash 4 MB/main stack 4096 via target sibling. Neither is board validation or a
  stack sufficiency claim. Minimal components do not support all optional modes.
- Defaults are requested settings; effective sdkconfig is authoritative. Snapshots
  do not automatically capture referenced CSVs/env inputs. No hermetic/bit-identical
  promise. Artifacts/sources/configs are ignored locally; reviewed hashes tracked.

## Verification

- python3 -m unittest discover -s tests -p test_scalar_tools.py -v: PASS, 28 cases
  with additional table-driven subcases, no SDK/hardware needed. Covers snapshots/
  siblings/symlinks/mutation, policy, JSON/path/hash boundaries, CLI behavior,
  mismatches, incomplete/faulted logs, sample/debugger semantics and input limits.
- Control and test-4mb scalar probes: PASS, 75 commands each, 18 expected failures
  each; four target builds O0/O2 total. All prior target/host bridge, ABI/policy,
  arithmetic compile/dependency and application sequencing checks pass.
- Explicit overlay effective values verified: 4 MB flash and 4096-byte stack;
  control 2 MB/3584. Image descriptor full ELF hashes match all four ELF files.
- Six supplementary strict host application compile/run checks at the final
  test-source revision pass at O0/O2.
- Four synthetic CLI captures against actual build manifests: consistent, with
  physical proof false. Wrong-manifest selection rejected. Two SDK configuration
  experiments reject incompatible panic and unknown Kconfig before build, retain
  failed status and publish no manifest.
- App images control and overlay: O0 146144 / O2 145824 bytes (same sizes, different
  hashes). Five known generated unused warnings per level; no new app warning or
  suppression. Effective configs/artifacts/default snapshots checked by hashes.
- Python syntax, local Markdown, Git whitespace and evidence integrity at final
  checkpoint. SDK/Goose references clean. Broad compiler/runtime suites not rerun:
  those implementations unchanged. Physical/simulator/serial: NOT RUN.

## Incomplete / blockers

- Physical success/fatal behavior, real low-water readings and complete SDK/ROM/
  callback/exception/register-window stack analysis remain open. M2b blocks HAL.
- Exact module/board/flash/PSRAM/console details and explicit authorization before
  any concrete flash/monitor/debug operation. No board selected or certified.
- Full upstream compiler/LSP/sanitizer suites, license/distribution inventory and
  project license pending. No SDK/tool/generated binary redistribution.

## Files and Git

New: tools/{scalar_config.py,validate_scalar_run.py}, tests/test_scalar_tools.py,
tests/esp_idf/{stubs/esp_app_desc.h,configs/{four-mb.defaults,
four-mb.defaults.esp32s3,bad-policy.defaults,unknown.defaults}},
docs/RUN_LOG_FORMAT.md, research/{CONFIGURATION_LOG_VALIDATION.md,
configuration-log-results.json}. Updated: target probe, app_main/main CMake,
application host double, README/example/tools docs, architecture/roadmap/decision/
learning/hardware procedure/template and state/handoff. Compiler/panic unchanged.

Branch main; no remote. Prior verified stack checkpoint:
04b4b5aed7615ff3ea95d3eb5a28ba769cb34417. Current checkpoint is the commit
containing this file; resolve git log -1 and verify status. Task changes intended
to be committed together. An unrelated untracked .vscode/ appeared during work;
it is untouched and excluded from this checkpoint. Check status. Raw evidence in build/esp-idf-config-*
and build/config-fixtures; summary tracked. Fresh probe output required.

## Next action / model

Prepare separate success/fatal firmware case selection and expected-log checks
without physical execution; normal-path validator intentionally rejects panics.
Sol/medium for these bounded changes/tests. Astra/high for remaining full-stack/
exception/ROM safety reasoning. Keep board variants separate, no invented presets,
no HAL or hardware operation without prerequisites. No model switch or paid API.

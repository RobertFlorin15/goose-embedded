# Selectable scalar fatal cases — 2026-11-05

**Result:** success, cold-export and overflow compile/link for ESP32-S3 at O0/O2.
Actual application + generated runtime + real SDK panic adapter execute on the
host with SDK doubles. Saved-file normal/fatal checks pass synthetic fixtures and
reject mismatches. **No physical/simulator execution, SDK panic-handler execution,
observed halt, device capture or full task stack bound. M2b and HAL remain gated.**

## Acceptance criteria and implementation

- Explicit compile-time case selection, default success; unknown cases rejected
  by CLI/CMake and application preprocessor guard.
- Cold export and checked overflow invoke the actual runtime; no new runtime or
  panic-adapter behavior. A returning failure emits a different message.
- Per-case/level manifests and actual compile-definition checks distinguish builds.
- Normal/fatal offline validators reject each other's case. Shared integrity
  loading retains prior hash, path, JSON, config and input-limit checks.
- Expected message/halt/order checks with rejection tests and honest proof flags.

All criteria pass at the evidence levels above. [Protocol](../docs/FATAL_RUN_LOG_FORMAT.md)
provides exact diagnostics and source permalinks. Implementation is confined to
example configuration/application, build/check tools and tests; compiler patches,
SDK panic adapter and pins are unchanged. No HAL/peripheral abstraction added.

## Reproduce

With the existing pinned setup in [tools](../tools/README.md), use fresh outputs:

```sh
python3 -m unittest discover -s tests -p 'test_scalar*.py' -v
python3 tools/test_esp_idf_scalar.py --case cold-export --output build/esp-idf-fatal-cold
python3 tools/test_esp_idf_scalar.py --case overflow --output build/esp-idf-fatal-overflow
python3 tools/test_esp_idf_scalar.py --output build/esp-idf-fatal-success
```

Recorded outputs use those exact paths. Each probe passes 83 commands, including
22 expected nonzero results. Eight additional commands per configuration compile/
execute the two actual fatal applications on the host at both optimization levels.
All previous target ABI/leaf/arithmetic/dependency, panic policy, normal app and
watermark-unit checks remain enabled. SDK/Goose reference trees remain clean.

| Firmware case | O0 app bytes | O2 app bytes | app_main frame O0/O2 |
|---|---:|---:|---:|
| success | 146144 | 145824 | 48 / 48 bytes |
| cold-export | 145808 | 145520 | 48 / 32 bytes |
| overflow | 145872 | 145600 | 48 / 32 bytes |

These are compilation sizes, not runtime footprint/stack bounds. Whole task,
SDK/ROM, windows, interrupts and exceptions remain unresolved. Effective control
configuration remains 2 MB flash, 3584-byte main stack; this is no board preset or
proof of sufficient stack. esptool confirms full ELF hash embedded in all images.

## Host and saved-file checks

41 unittest cases (29 normal/config/integrity + 12 fatal, with table subcases) pass.
Fatal coverage includes both categories, missing/duplicate/reordered cues, wrong
identity/case/artifact, partial debugger record, normal telemetry, unrelated faults,
reset/reboot, truncated capture, output after halt and CLI status. A declared
physical evidence type still yields no physical proof.

27 supplementary checks pass: six synthetic logs against actual build manifests;
six opposite-validator rejections; one cross-case manifest mismatch; twelve host
wrong-case marker rejections (exit94); CMake and C preprocessor unknown-case
rejections. Six actual compile databases match their selected case. The permanent
probe gained this definition guard after the six builds; the equivalent guard was
run separately against all six databases. No firmware/source change followed.

Synthetic capture recipe: UTF-8 LF log starts with the explicit SYNTHETIC notice,
then identity with the selected manifest ELF hash. Normal logs contain result 42,
stack values 3000/2800/2400 and completion; fatal logs contain selected case,
expected details and CPU halted. Captures declare synthetic, selected case/config/
level, manifest/log SHA256 and relative serial.log. This uses invented test values
only. No SDK backtrace or physical measurements are fabricated. Re-run the
appropriate validator from the protocol documents with the selected manifest/
capture; using the other validator must reject.

Raw logs/manifests/captures: build/esp-idf-fatal-{cold,overflow,success},
build/fatal-fixtures. [Tracked summary](fatal-case-results.json) records hashes,
commands/results and per-image evidence. Generated artifacts stay ignored.

One supplementary script initially used a nonexistent generated-header directory;
its expected preprocessor-diagnostic assertion failed on a missing header instead.
Corrected to firmware/esp-idf/goose_scalar; the intended unknown-case rejection
then passed. This was a test-harness path error, not a target/runtime failure.

## Limits / next task

A halt cue is printed before the SDK's final halt routine. File consistency cannot
prove execution, halt or stack safety. Known unrelated diagnostic patterns are
rejected; unknown faults still require human log review. No actual board/config/
console inventory or hardware authorization exists. Multiple board variants need
separate future settings/evidence. Never flash generic test configurations.

Next: source/assembly audit of these fatal entry paths and remaining SDK/exception
stack requirements, explicitly listing what cannot be bounded without exact
ROM/board evidence. Astra/high is appropriate if pursuing complete stack reasoning;
Sol/medium is sufficient for routine tool maintenance. Keep M2b/hardware and HAL
gates unchanged; license/distribution review also remains pending.

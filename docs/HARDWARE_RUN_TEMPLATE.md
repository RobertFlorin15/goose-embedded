# ESP32-S3 validation record — UNEXECUTED TEMPLATE

Copy this into a configuration-specific research record when an actual board and
reviewed build are selected. No authorization or hardware result is implied here.
Keep distinct records for differing modules/flash/PSRAM/console settings.

## Identity and authorization

- Date/operator: unrecorded
- Board/carrier revision and module marking: unidentified
- Authoritative schematic/module reference: unrecorded
- Silicon revision, flash type/size/mode/frequency, PSRAM type/size/mode: unknown
- Console routing and port: unselected
- Explicit authorized action and its scope: none

## Reproducible build

- Project branch/commit and dirty status: unrecorded
- Goose pin/patch digests and compiler binary/version: unrecorded
- SDK commit/submodules/toolchain/Python lock identity: unrecorded
- Build command/output directory, optimization and actual sdkconfig/hash: unrecorded
- Flash/PSRAM/console/partition/stack/panic settings reviewed against board: no
- Application/bootloader/partition image hashes and map: unrecorded
- Source and config gates pass for this configuration: not checked
- Flash command/image/offsets reviewed from build metadata: not prepared

## Physical evidence (not host-double or compile results)

- Exact authorized commands executed: none
- Boot/full serial log path and hash: none
- Expected result line: `goose-embedded scalar-v0: 42` — NOT OBSERVED
- Stack report syntax: `goose-embedded stack-v1: before=N after_goose=N after_result_print=N bytes`
- Actual readings: none; N is a placeholder, not a measurement
- Debugger record ge_stack_samples (completed, all four fields): unread
- Resets/boot problems/console loss and observation duration: unrecorded
- Result: UNEXECUTED

The report contains the first three lifetime low-water readings. The fourth
(after_report) is debugger-only so the act of reporting is not excluded silently.
completed=4 is required for a full normal-path record; a partial record after a
fatal error must be labeled partial. Samples precede main-task deletion; inspect
the completed record as a snapshot, not a live task handle. Scans include prior SDK work and instrumentation and
can miss untouched reserved frame space. Do not treat deltas as isolated Goose
consumption or a nonzero reading as a stack-safety certificate. No reading covers
the SDK return log/task deletion after app_main, or a future fatal workload.

## Separate fatal-case records

- Reviewed fatal firmware variant/source/config/image identity: none
- Explicit authorization for this case: none
- Overflow/lifecycle case and expected SDK panic policy: unselected
- Actual diagnostic/halt/reset log and source record: none
- Stack/exception-path evidence and limitations: unverified
- Result: UNEXECUTED

## Review

- Supported claim for this exact configuration/workload: none
- Unresolved stack/ROM/exception/panic questions: unreviewed
- Links: [hardware procedure](HARDWARE_VALIDATION.md),
  [stack audit](../research/STACK_MEASUREMENT.md)

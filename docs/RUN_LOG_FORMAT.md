# Configuration inputs and saved-run consistency (v1)

The build helper accepts an ordered list of ESP-IDF defaults files. The example's
base policy is first; repeated --defaults append overlays. An explicit --config-id
is required with overlays. Labels identify configurations, not verified boards.

```sh
python3 tools/test_esp_idf_scalar.py --config-id my-config --defaults /path/to/reviewed.defaults --output build/my-config
```

The helper snapshots input bytes in config-inputs/ and records their SHA-256 and
original paths. It preserves each input's optional .esp32s3 sibling and ordering,
including lookup beside a supplied symlink path. Snapshots are files, not links.
Missing/duplicate inputs and CMake list/newline path delimiters are rejected.
Source/snapshot changes are detected. Original paths are provenance metadata;
snapshot paths are relative to the probe output root, not each O0/O2 directory.

SDKCONFIG_DEFAULTS receives only the snapshots; each fresh O0/O2 tree gets its
own effective sdkconfig. Unknown-symbol notes and incompatible effective target/
panic/LTO settings fail before compilation; the C policy guard remains in place
for manual builds. SDK dependency/range rules can affect requested options: read
the effective sdkconfig, not only the defaults. Referenced files such as custom
partition CSVs still need their own review/provenance. This is not hermetic setup
or a claim that every board/PSRAM mode is supported by the minimal component set.

After the full probe passes, each level receives run-manifest.json. It contains
schema/kind, configuration label, optimization, SDK/compiler identity, defaults
metadata, configured main-stack size and hashes for the effective sdkconfig,
ELF, app image, bootloader and partition image. Keep those files in their original
relative layout if copying the manifest; the offline validator requires them.
Honor the build helper exit status and preserve failed outputs as failed evidence.

## Telemetry protocol

The current example emits these four plain lines, with real values filled at
runtime. No such device capture exists yet:

```text
goose-embedded identity-v1: elf_sha256=<full 64 lowercase hex digits>
goose-embedded scalar-v0: 42
goose-embedded stack-v1: before=N after_goose=N after_result_print=N bytes
goose-embedded completed-v1
```

The identity is the full ELF SHA-256 from the running image's SDK descriptor,
converted in fixed static storage. It avoids the SDK default abbreviated hash.
The probe checks esptool image-info against the actual ELF hash. This is an ELF
fingerprint, not authentication or independent attestation of every config bit.
The manifest associates the reviewed config/artifacts with that ELF.

Identity printing precedes the before sample, so its touched stack space can
influence all lifetime low-water readings. Completion is printed only after the
debugger-only after_report sample and completed=4 store. That final marker print
and subsequent SDK return/deletion are not covered by the four readings.
The marker shows application progress in a supplied log, not successful RTOS
task deletion or a measured whole-task stack bound. Fatal cases use separate
records and are not accepted by this normal-path validator.

## Capture JSON

Create a separate record beside the raw UTF-8 log. Placeholders below must be
replaced; they are not a valid capture or a hardware result:

```json
{
  "schema_version": 1,
  "kind": "scalar-v0-capture",
  "evidence_type": "unknown",
  "manifest_sha256": "<SHA-256 of the selected run-manifest.json>",
  "configuration": "my-config",
  "optimization": 0,
  "log": "capture.log",
  "log_sha256": "<SHA-256 of capture.log>"
}
```

evidence_type must be synthetic, physical, simulator or unknown. It is an
operator declaration, never authenticated by the parser. Optional debugger is
an object with integer fields before, after_goose, after_result_print,
after_report, completed. If provided, completed must be 4, the first three must
match serial, and after_report must be in range and no larger than the prior
reading. A missing debugger record stays null; serial does not contain that
fourth numeric value. Never reuse stale fields from a partial debugger record.

```sh
python3 tools/validate_scalar_run.py --manifest build/my-config/O0/run-manifest.json --capture research/runs/my-config/capture.json
```

The command reads saved files only and writes JSON to stdout. Exit 0 means
consistent; exit 1 means rejected. It verifies hashes, config label/level, known
target/panic policy, complete ordered telemetry and firmware identity. Log paths
must remain inside the capture directory; artifact paths stay inside the manifest
directory. Symlink escapes and duplicate JSON keys fail. Maximum log size is
16 MiB; inputs are never silently truncated. LF and CRLF are supported; timestamp
wrappers/ANSI decoration on protocol lines are not normalized automatically.

Missing, duplicate, malformed or out-of-order protocol lines are rejected, as
are known panic/assertion/stack/watchdog diagnostics and resets/second boots.
Readings must fit the configured stack range and be non-increasing; anomalies
require review. Zero is accepted as data and flagged, not treated as safe.
Checks cover the supplied text, not unknown failures or events after capture.

Every success explicitly has hardware_execution_proven=false and
stack_bound_proven=false. Edited logs and manifests can be mutually consistent;
no parser can establish physical execution, authorization, correct board identity
or stack safety from these files alone. Human review and actual evidence remain
in [the hardware procedure](HARDWARE_VALIDATION.md) and
[run template](HARDWARE_RUN_TEMPLATE.md). All automated fixtures so far are synthetic.

New manifests include `case`, with `success` for the normal application. Normal
captures may explicitly provide `"case": "success"`; omitted case in legacy
normal manifests/captures means success. The normal checker rejects fatal build
cases even if supplied text resembles normal telemetry. Use the separate
[fatal-case protocol/checker](FATAL_RUN_LOG_FORMAT.md) for cold-export/overflow.

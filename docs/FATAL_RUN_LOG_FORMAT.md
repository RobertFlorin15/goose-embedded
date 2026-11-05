# Fatal firmware cases and saved diagnostics (v1)

These are deliberate failure experiments, built separately from the default
success application. Building does not authorize flashing, monitoring or debugging.
No physical diagnostic has been observed. Review exact board/configuration and
obtain hardware authorization using [the hardware procedure](HARDWARE_VALIDATION.md).

```sh
python3 tools/test_esp_idf_scalar.py --case cold-export --output build/cold-new
python3 tools/test_esp_idf_scalar.py --case overflow --output build/overflow-new
```

Each command builds O0/O2, runs host tests and publishes separate manifests after
all checks pass. `--case success` is the default. Configuration overlays and IDs
work identically for all cases. Direct CMake builds use GE_SCALAR_CASE with one of
these exact names; unsupported names fail configuration. The main component maps
names to reviewed compile-time cases, with no runtime console selection.

| Case | Deliberate operation | Expected SDK abort details |
|---|---|---|
| cold-export | ge_add(10,32) before goose_init | goose_init must be called before exported functions |
| overflow | goose_init(0,NULL), ge_add(INT32_MAX,1) | i32 overflow |

Both cases print full ELF identity, take only the first watermark sample, set
completed=1, print the case marker and invoke the operation. No success/result,
stack report, completion marker or goose_exit is expected. The panic bridge is
unchanged. A returning operation invokes a different, rejected panic message:
`fatal case unexpectedly returned`. The debugger stack record is partial; do not
submit it as a complete normal-run measurement. Source location for overflow is
stored by the bridge; cold export has NULL file/line zero. These are host verified,
not observations from a target panic.

Expected plain protocol and diagnostic cues (placeholders, not a real capture):

```text
goose-embedded identity-v1: elf_sha256=<full ELF hash>
goose-embedded case-v1: overflow
i32 overflow
<SDK state/backtrace and abbreviated ELF information, if present>
CPU halted.
```

Pinned SDK 7101770dc6db2667b3c477cc31365dd1acd6db4e prints supplied abort details
verbatim in [panic.c](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/panic.c#L173),
clears reason/description for abort (L294), and prints the halt cue under this
policy (L454). `esp_system_abort` forwards directly to panic_abort in
[esp_system_chip.c](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/port/esp_system_chip.c#L85).
Do not expect libc abort's `abort() was called` message or Guru Meditation banner
for this direct binding. Addresses/backtrace frames are not fixed parser inputs.

Use the [v1 capture record](RUN_LOG_FORMAT.md), adding `"case": "overflow"` or
`"case": "cold-export"`. The manifest and capture must explicitly agree. New
manifests always contain case; only normal success records permit the legacy
omitted case, interpreted as success. Schema/kind remain v1; unknown cases fail.
Do not attach the normal stack `debugger` object to fatal captures.

```sh
python3 tools/validate_scalar_fatal.py --manifest build/overflow-new/O0/run-manifest.json --capture /path/to/capture.json
```

The shared loader checks artifacts, effective policy, configuration, case,
optimization, ELF identity, record/log hashes, paths and input limits exactly as
for normal runs. The separate fatal checker requires one identity/case pair and
one expected details line followed by one terminal halt cue. It rejects missing,
duplicate, conflicting or reordered cues, normal protocol, known unrelated faults,
resets, SDK |<-CORRUPTED backtraces, and nonempty content after halt.
A |<-CONTINUES depth-limit marker remains allowed and requires human review;
it does not certify a complete backtrace. Unknown fault text cannot be exhaustively
recognized; human review of the complete retained log remains necessary.

Exit 0/status consistent means supplied files agree. The result always keeps
hardware_execution_proven, halt_proven and stack_bound_proven false. Even a real
printed halt cue precedes the SDK's final halt routine and cannot prove physical
halt occurred or persisted. Synthetic fixtures exercise parsing only; neither
host doubles nor target compilation execute the SDK panic handler.

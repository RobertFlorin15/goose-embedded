# Handoff

2026-11-05. **Stack observation code cross-builds and host tests pass. No target
readings, execution, simulator, serial or flash. Whole task stack bound OPEN.**

Recover AGENTS.md -> PROJECT_STATE.md -> project skill -> Git/source/evidence.
Branch main, no remote. Previous integration cbebb2f660a4a9c8d02cc9003e0f5394d8039c4e.
Current checkpoint is the commit containing this handoff (git log -1 resolves it).
Task changes intended to be committed together; verify status. SDK and clean
Goose reference checkouts unchanged. Compiler/runtime patches and panic binding
unchanged; no HAL. M2a leaf cross-build gate passes, M2b remains unverified.

New app_main reads uxTaskGetStackHighWaterMark(NULL) four times: before/after
Goose, after result printing and after reporting. Pinned API uses bytes; one-byte
StackType_t/API/integer-width guards compile. First three readings printed in
stack-v1 line, fourth only in volatile ge_stack_samples.after_report. completed
0..4 marks valid fields (reset at entry). Target pointer/prototype checks moved
intact to abi_checks.c, included/required by CMake/probe. Actual app_main runs in
Linux tests using SDK/Goose doubles, no macro disabling target assertions.

Verified command:
```sh
python3 tools/test_esp_idf_scalar.py --output build/esp-idf-stack-probe
```
PASS: 73 commands, 18 expected failures; target O0/O2, original bridge/ABI/policy
checks, actual app sequencing/reset/units/reporting/early-panic host tests,
wide-stack-element compile refusal. Eleven supplementary read-only SDK/ROM
inspection commands pass. Images 145888/O0, 145616/O2 bytes; bootloader 21040.
Five known generated unused warnings per level, no new app warning/suppression.
Full logs/ELFs in build/esp-idf-stack-probe; ROM/extra SDK audit logs in
build/esp-idf-stack-audit. Reviewed research/STACK_MEASUREMENT.md and its JSON
preserve code/artifact/log hashes; hardware_samples is null. Fake numbers in
host tests are test data, NEVER device evidence. Earlier broad host suites not
rerun because compiler/runtime unchanged.

Audit: SDK wrapper/main_task add 80 visible parent-frame bytes; individual app
frame remains 48. Partial normal arithmetic path incl. parents 304/O0,160/O2;
sampler path 192. User exception entry adds 192 task-stack bytes before C
handling; ordinary interrupt stack switch is distinct. Official revision-0 ROM
ELF contains real printf code with indirect callbacks; silicon revision and
callback configuration unknown. These are partial frame observations, not a
whole 3584-byte stack bound. Fill scanning includes prior SDK/instrumentation
and can miss untouched reservations. No measurements in panic, no after-return
coverage, no ISR/cache-off/concurrent support.

User wants future coverage across several ESP32-S3 board types. No exact
inventory/settings or hardware authorization supplied. Keep flash/PSRAM/console/
pin choices separate from runtime; current DIO/2 MB/no-enabled-PSRAM config is
not universal. docs/HARDWARE_RUN_TEMPLATE.md is UNEXECUTED, not a filled record.

Next exact task: support explicit SDK configuration-overlay inputs and offline
run/log validation against build identity, with tests of mismatches/partial
records. Do not fabricate board definitions. Before any physical operation,
identify/review a configuration and obtain explicit authorization; success/fatal
cases need separate physical evidence. Remaining stack-bound review may merit
Astra/high; Sol/medium suffices for configuration/log tools. No model switch.

Pins unchanged: Goose 335fddc13dc74666398ffe160ec8a8f2958329d0 plus 0001/0002;
.cache/goose-scalar-runtime, build/goose-scalar-runtime/goose. ESP-IDF v6.0.2 at
7101770dc6db2667b3c477cc31365dd1acd6db4e / 25 submodules in .cache/esp-idf-v6.0.2;
.cache/espressif GCC 15.2.0/esp-15.2.0_20251204. Exact Python lock in tools/;
host Python 3.14.4/CMake 4.2.3/Ninja 1.13.2. Fresh probe output required (existing
path refuses overwrite). Setup in tools/README.md. License inventory/full upstream
suites remain open. Grapify unavailable in prior checks; standard tools used.

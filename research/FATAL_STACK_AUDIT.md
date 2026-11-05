# Fatal-path stack audit — 2026-11-05

**Static source/artifact inspection only.** Four previously passing fatal ELFs
were re-inspected. No new firmware build, target execution, physical reading or
complete stack bound. The 3584-byte main stack is still a configuration value,
not a verified sufficient budget. M2b and HAL remain gated.

Starting checkpoint: 4352678ac2b2d580e40eee218c82ef7d42be09a2.
Pins: Goose 335fddc13dc74666398ffe160ec8a8f2958329d0 plus existing scalar patches;
ESP-IDF 7101770dc6db2667b3c477cc31365dd1acd6db4e; esp-15.2.0_20251204 GCC 15.2.0.
No compiler/runtime/application/panic-adapter change. Offline fatal validation
now rejects the SDK's corrupted-backtrace marker.

## Reproduce and acceptance

```sh
python3 tools/audit_scalar_fatal.py --build build/esp-idf-fatal-cold --build build/esp-idf-fatal-overflow --output build/fatal-stack-audit-final
python3 -m unittest discover -s tests -p 'test_scalar*.py' -v
```

Prepare missing build inputs using [the fatal-case probe](FATAL_CASES.md); use a
fresh audit output. The tool verifies the pinned clean SDK/submodules, passing
probe, current recorded example/adapter sources and manifest/artifact hashes.
It checks ELF identity against the passing probe, retains four disassemblies and
extracts 140 individual-symbol records. Unknown/assembly frame sizes remain null,
never zero. Missing symbols/multiple entry instructions fail for manual review.
The manually reviewed pre-trap paths are explicitly not automatic reachability
or whole-call-graph analysis. Indirect calls and unresolved offset names remain
visible; no inferred zero cost is assigned. Scope is the current UART plus
secondary USB Serial/JTAG console configuration; other selections need review.

Acceptance: trace fatal entry to SDK halt with source/assembly evidence; identify
stack ownership and active versus sequential frames; enumerate missing bounds;
reject any newly identified fault cue. These criteria pass. A full stack bound
is intentionally not an acceptance claim of this bounded audit.

## Reviewed paths before the trap

Cold export: wrapper -> main_task -> app_main -> ge_add -> gs_panic (O0 only)
-> scalar hook -> esp_system_abort -> panic_abort -> illegal instruction.

Overflow: wrapper -> main_task -> app_main -> ge_add -> add_g -> gs_add_i32
-> gs_scalar_overflow (three helpers visible O0 only) -> scalar hook
-> esp_system_abort -> panic_abort -> illegal instruction.

At O2 helper bodies are folded into ge_add. Calls to goose_init, identity/case
ROM printing and watermark scanning return before the fatal chain; do not add
their frames to its simultaneous nesting. Their earlier stack peak still matters
for the whole-task lifetime budget. Source: [app_main](../examples/esp32s3_scalar/main/app_main.c),
[adapter](../src/platform/esp_idf/scalar_panic.c), generated C in each build tree;
SDK [abort forwarding](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/port/esp_system_chip.c#L85)
and [panic_abort](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/panic.c#L461).

| Individual entry frame | O0 bytes | O2 bytes |
|---|---:|---:|
| vPortTaskWrapper / main_task |32 /48 |32 /48 |
| app_main / ge_add / scalar hook |48 /48 /48 |32 /32 /32 |
| gs_panic (cold only) |48 |inlined |
| add_g / gs_add_i32 / gs_scalar_overflow (overflow only) |64 /64 /48 |inlined |
| esp_system_abort / panic_abort |32 /32 |32 /32 |
| Cold visible pre-trap sum |336 |240 |
| Overflow visible pre-trap sum |464 |240 |

These sums count reviewed entry instructions including SDK parents. They exclude
exception/context/diagnostic work and are not a memory bound or safe threshold.
SDK component optimization stays at SDK settings; only example/generated code
uses selected O0/O2. Helpers present in an ELF need not be active in a given case.

## Exception ownership and memory touches

The [ordinary user exception path](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/xtensa/xtensa_vectors.S#L741)
stays on the user/task stack. Linked _xt_handle_exc subtracts 256, adds 64: a net
192-byte exception allocation. It also performs s32e stores at new a1-12/-16 for
the pseudo backtrace save area. Thus one explicit store address is 208 bytes below
the trapped a1, before C diagnostic frames. Do not equate allocation with deepest
touched byte, or blindly add another 16 to every later C-frame sum: save areas can
overlap ABI-reserved areas. An ABI-aware peak analysis is still required.

[_xt_context_save](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/xtensa/xtensa_context.S#L107)
saves into this frame, temporarily returns sp to the spill region, flushes live
windows and restores sp. [The spill macro](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/xtensa/include/xt_asm_utils.h#L51)
rotates register windows; the linked window-overflow vectors write into ABI save
areas of ancestor frames. These routines have no ordinary entry frame; null in
the extractor means unaccounted assembly behavior, not free stack usage. Adding
an arbitrary per-window constant risks both undercounting and double counting.

The exception dispatch table is initialized to xt_unhandled_exception in
[xtensa_intr_asm.S](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/xtensa/xtensa_intr_asm.S#L132).
Dispatch uses an indirect call; the registration API can replace it. This audit
assumes the reviewed application does not install a replacement. It is not a
runtime attestation of table contents.

By contrast, [level1 interrupt dispatch](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/xtensa/xtensa_vectors.S#L1220)
allocates context then enters the RTOS system stack. Its configured 1536 bytes
are not a separate emergency stack for this ordinary fatal chain. Other exception,
nested-interrupt and double-fault paths need their own ownership analysis.

## SDK diagnostics and halt

xt_unhandled_exception calls panic_enable_cache, then panic_handler(frame,false).
Cache preparation returns before the latter; its 32-byte frame is sequential.
Linked panic_handler is 80 bytes, including panic_info local; esp_panic_handler
is 32 bytes. The low-level entry/cache helper are IRAM; the current panic_handler
and esp_panic_handler are flash code (CONFIG_ESP_PANIC_HANDLER_IRAM unset). Source
comments alone do not establish placement; inspect linked sections. The SDK cache
preparation does not broaden Goose's normal-task/cache-enabled contract.

[panic_handler](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/port/panic_handler.c#L127)
tracks entry count, prepares watchdogs, coordinates/stalls the other core, builds
panic_info and calls the generic handler. These calls include ROM/indirect paths;
no complete inclusive cost was established. Multicore SDK behavior exists even
though Goose has only one serial caller.

[State callbacks](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/port/panic_handler.c#L58)
retain a backtrace on Xtensa abort while suppressing the register dump. Callback
frames: print_state 32, print_state_for_core 32, panic_print_backtrace 48,
esp_backtrace_print_from_frame 48. The [walker](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/port/arch/xtensa/debug_helpers.c#L57)
is iterative with depth argument 100, not 100 recursively nested C frames. It checks
frame sanity and can emit |<-CORRUPTED or |<-CONTINUES. Fatal saved-file checks
now reject corruption; the bounded continuation marker remains allowed, without
claiming a complete or correct backtrace. SDK state callbacks can also inspect a
second core's saved frame when present.

Panic output uses [panic_print_str/char](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/panic.c#L83),
not the normal application's ROM printf formatter. Compiled frames: str 32,
char 32, UART character 64, uart_hal_write_txfifo 32, secondary USB character 48.
UART and secondary USB character functions are called sequentially; summing both
as nested would be wrong. USB may call ROM delay while polling; UART may wait
for FIFO capacity. No target timing, physical delivery or full output cost is
proved. Secondary USB is enabled in current control sdkconfig, regardless of a
future board's chosen cable/console. The earlier ROM formatter audit still applies
to normal identity/case prints; it cannot substitute for this panic output path.

The [halt stub](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_system/panic.c#L259)
has 32 bytes and calls module-reset code (32), which first waits for UART output
through a ROM service before resetting modules and reaching the infinite loop.
Therefore even the printed halt cue precedes further calls, possible waiting and
peripheral resets. This is why halt_proven remains false. No such operation was
executed on hardware in this audit.

## Unclosed requirements

| Missing evidence | What closes it |
|---|---|
| Pre-app/identity/case/SDK return lifetime peaks | Review full normal call paths and actual ROM output callbacks/revision; authorized measurements supplement static reasoning |
| Window/exception save-area peak and overlap | ABI-aware instruction/memory analysis of linked context and window vectors; include active ancestor frames |
| SDK panic callbacks/watchdog/console/reset inclusives | Resolve indirect/ROM callees and branch configurations; treat sequential calls as maxima and nested calls as sums |
| Interrupt nesting and other-core conditions | Document enabled interrupts, stack domains and permitted panic scenarios for each reviewed config |
| Hardware normal/fatal behavior and output delivery | Exact reviewed module/flash/PSRAM/console configuration plus explicit authorization and retained physical evidence |
| Sufficient stack and final/persistent halt | Complete justified budget with explicit assumptions plus relevant device observations; no inference from text alone |

No arbitrary headroom/stack increase or custom panic-stack runtime is introduced.
A separate panic stack is an architectural change needing ABI/double-fault review,
not a shortcut supported by this analysis. Until requirements close, do not label
these firmware images stack-safe or a universal ESP32-S3 build.

## Verification and next task

Four fatal ELF inspections /140 symbol records pass, with artifact/source/SDK
hash checks. 47 unit tests pass, including five extractor boundary/unknown-frame
tests, corrupted-backtrace rejection and allowed continuation. Four audit refusal
checks pass (normal build, existing output, input-tree overlap, tampered ELF); six
previous synthetic captures still validate. No target rebuild is needed: only
host audit/offline parsing and docs changed. Previous six cross-build results
remain historical compilation evidence. No physical/simulator tests run.

Raw logs: build/fatal-stack-audit-final, build/fatal-audit-unit-tests.log,
build/fatal-audit-refusals. [Tracked summary](fatal-stack-results.json) binds file
hashes, reviewed frame paths and checks. SDK/Goose references stay clean. Grapify
unavailable in prior discovery; standard pinned-source/disassembly tools used.

Next independently actionable work: inventory licenses/distribution obligations
of pinned compiler, SDK and installed tools before choosing a project license.
Sol/medium suits file-based inventory; retain exact texts/paths and avoid legal
compatibility claims without review. Astra/high remains recommended for closing
ABI/window/exception/ROM stack analysis. No hardware or HAL work follows this audit.

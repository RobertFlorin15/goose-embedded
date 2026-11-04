# Handoff

2026-11-05. **Scalar leaf links for ESP32-S3 at -O0/-O2. No target execution,
serial observation, flashing or HAL. Whole task stack budget is still open.**

Recover AGENTS.md -> PROJECT_STATE.md -> project skill -> Git/source/evidence.
Branch main, no remote. Prior SDK checkpoint 80043c9afa26d6d17e0a474329d9db8ae16e259e.
Integration checkpoint is the commit containing this handoff (git log -1 resolves
it). Task changes intended to be committed together and status checked clean;
verify Git. Reference .cache/goose and SDK checkouts remain clean.

Durable implementation: existing compiler patches/goose/0001+0002 unchanged;
new examples/esp32s3_scalar generates leaf C/header as an ESP-IDF component,
with separate app_main and src/platform/esp_idf/scalar_panic.c. App checks ABI,
initializes, calls ge_add(10,32), checks 42, exits and requests ROM console output.
Expected line goose-embedded scalar-v0: 42 has NOT been observed on hardware.
Panic hook stores static diagnostic pointers/line in volatile debugger record,
then calls SDK esp_system_abort. ABI/minimal halt-policy compile guards; no
formatting/allocation in adapter. No ISR/cache-off/reentrant/concurrent support.

Verified: tools/test_esp_idf_scalar.py final run build/esp-idf-scalar-verified
passes 53 commands (14 expected failures); two firmware builds, 12 Linux bridge
runs with terminating SDK double, four ABI/policy compile refusals. Target leaf/
arithmetic imports exactly hook, bridge exactly esp_system_abort. ELF/map/ABI/
assembly/config checks pass, LTO off. SDK prefix calls panic_abort then ill, no
allocator/formatter before trap. Physical SDK panic handling is not tested.
Five known generated unused warnings per level remain; no new suppression.
Earlier configure ordering and unknown-default issues corrected and recorded.

Images: O0 145584, O2 145376 bytes; bootloader 21040. Partial compiler frames:
normal call path 224/O0, 80/O2; overflow to SDK trap 384/O0, 176/O2. These omit
SDK entry, ROM, exception/interrupt/register-window/diagnostic costs and DO NOT
prove the configured 3584-byte main stack sufficient. No firmware-wide no-heap
or general Goose-language portability claim. M2a leaf cross-build/ABI gate passes;
M2b remains unverified and blocks HAL.

User steering: has several ESP32-S3 board types and wants future support across
all. No exact inventory/settings or hardware authorization supplied. Keep board
flash/PSRAM/console/pin details separate from runtime; current SDK DIO/2 MB/
no-enabled-PSRAM control image is not universal. docs/HARDWARE_VALIDATION.md
records per-configuration evidence requirements. Do not repeatedly ask for one
board as if it defines the framework; identify a configuration before execution.

Pins/cache: Goose 335fddc13dc74666398ffe160ec8a8f2958329d0, prepared source
.cache/goose-scalar-runtime and build/goose-scalar-runtime/goose (version
335fddc+scalar-v0-runtime, desktop runtime d22ae129d92b). SDK .cache/esp-idf-v6.0.2
at 7101770dc6db2667b3c477cc31365dd1acd6db4e, 25 recursive submodules, project-local
.cache/espressif tools/Xtensa GCC 15.2.0. Host Python 3.14.4/CMake 4.2.3/Ninja
1.13.2; exact Python package lock in tools/. Setup/reproduction in tools/README.md.

Exact next steps:
1. Read research/ESP32S3_SCALAR.md, its reviewed JSON and docs/HARDWARE_VALIDATION.md.
2. Audit missing main-task/ROM/panic stack paths; prepare bounded native stack
   measurement instrumentation, without widening the Goose profile or using HAL.
3. Prepare configuration-specific M2b record(s); review actual module/flash/PSRAM/
   console settings when available. Obtain explicit authorization before any
   concrete flash/serial operation. Success/fatal cases need physical logs.
4. Checkpoint before hardware/model transitions. Sol/medium for preparation;
   Astra/high if stack/exception reasoning needs deeper review.

Commands:
```sh
git status --short --branch
git log -3 --oneline
python3 tools/test_esp_idf_scalar.py --output build/esp-idf-scalar-next
```
Fresh output required. Script checks pins/source digests/package lock and records
binary hash; cannot prove arbitrary compiler provenance. Full ignored results in
build/esp-idf-scalar-verified, reviewed hashes/log/frame/dependency summary tracked
in research/esp32s3-scalar-results.json. Earlier broad host suites remain historical
PASS and were not rerun because patches unchanged. Grapify unavailable in prior
checks; full upstream suite/release license inventory remain open.

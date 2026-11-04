# Handoff

2026-11-05. **Official ESP32-S3 SDK baseline builds; Goose target integration is
next. No Goose Xtensa build, simulator/physical execution or HAL yet.**

Recover AGENTS.md -> PROJECT_STATE.md -> project skill -> Git/source/evidence.
Branch main, no remote. Prior runtime host checkpoint a66006f33fea11078472a168c2037096f5c559ed.
SDK checkpoint is the commit containing this handoff (git log -1 resolves it).
Task changes intended to be committed together, then status checked clean; verify
rather than trusting this note. No upstream checkout modifications.

Current SDK: .cache/esp-idf-v6.0.2, commit
7101770dc6db2667b3c477cc31365dd1acd6db4e; 25 recursive submodules pinned/clean.
Tools: .cache/espressif; Xtensa GCC 15.2.0 / esp-15.2.0_20251204. Pin/digests in
tools/esp-idf-pin.json; exact 58 Python packages in tools/esp-idf-python.lock.
Host Python 3.14.4/CMake 4.2.3/Ninja 1.13.2. Official install.sh and locked replay
on existing environment succeed; six downloaded archive hashes verified.

Verified baseline: python3 tools/esp_idf_baseline.py passes activation + five
commands, copies all six official hello_world files unchanged, sets esp32s3 and
builds through CMake with two jobs. ELF32/little-endian/Xtensa, app 145424 bytes;
bootloader/partition images and map present. Five helper refusals pass. No
warnings/errors detected in build/config logs. No execution implied. Full ignored
evidence in build/esp-idf-baseline; reviewed results/command/version/source and
artifact hashes in [ESP_IDF_BASELINE.md](../research/ESP_IDF_BASELINE.md) and its
linked JSON. Setup commands in tools/README.md. Outputs must be fresh.

Goose implementation is unchanged: patches/goose/0001+0002 and manifests prepare
.cache/goose-scalar-runtime, binary build/goose-scalar-runtime/goose (version
335fddc+scalar-v0-runtime, desktop runtime d22ae129d92b); clean source pin
335fddc13dc74666398ffe160ec8a8f2958329d0 in .cache/goose. Reproduce from patches
if absent; cache edits are not durable. Scalar runtime ABI 1 is host-tested only.
Required noreturn ge_scalar_v0_panic_v1(message,file,line); init only 0/NULL;
serial normal-task calls, no ISR/concurrency support. Preserve overflow/lifecycle
failure semantics and no-allocation hook contract. Linux panic hook is test code.
Historical 560 runtime/235 validator/32 desktop runtime command suites pass;
no rerun for this SDK-only task. [SCALAR_RUNTIME.md](../research/SCALAR_RUNTIME.md).

Exact next steps:
1. Read docs/SCALAR_PROFILE.md and the pinned SDK's panic/startup/task source/API.
2. Emit examples/leaf.goose with the scalar compiler, build as a separate ESP-IDF
   component with a minimal app_main and reviewed noreturn panic C binding.
3. Compare the linked target against the baseline; inspect generated object
   dependencies, Xtensa ABI/alignment, assembly/map and native stack assumptions.
   Baseline main-task stack is 3584 bytes; this is not a Goose stack budget proof.
4. Checkpoint evidence. Obtain board details and explicit authorization before
   any flash/serial operation. No HAL before M2 execution prerequisites pass.

Relevant commands:
```sh
git status --short --branch
git log -3 --oneline
python3 tools/esp_idf_baseline.py --output build/esp-idf-baseline-next
```
The helper checks clean SDK, exact tools manifest/GCC and installed package lock,
activates upstream environment in a child shell and does not access hardware.
For manual SDK commands export IDF_TOOLS_PATH="$PWD/.cache/espressif" before
sourcing .cache/esp-idf-v6.0.2/export.sh. Prefer child shells to avoid contaminating
host compiler tests. Installer constraints may change; review conflicts rather
than bypassing locks. No hermetic/bit-identical or firmware-wide no-heap claim.

Open: target binding/ABI/stack evidence, board data/authorization, full upstream
suite, release license inventory. Grapify unavailable in prior checks. Recommend
Sol/medium for narrow component integration, Astra/high for ABI/panic blockers.

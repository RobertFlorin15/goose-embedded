# Reference and license inventory

Read on 2026-11-04. Goose source is pinned in upstream.json. Other URLs below
are architectural reference snapshots of moving branches, not pinned dependencies.
The tracked Goose validator patch now contains upstream diff context; its
Apache-2.0 license is retained in patches/goose/LICENSE.upstream with modified-file
notices and provenance. No complete upstream tree or binary is vendored. Re-audit exact files
and transitive dependencies before selecting a project license or redistributing
compiler binaries/generated runtime code. This inventory is not a compatibility
clearance for future code copying.

| Project | Evidence inspected | Principle to retain | Constraint |
|---|---|---|---|
| [Goose](https://github.com/aardappel/goose/tree/335fddc13dc74666398ffe160ec8a8f2958329d0) | CMake, driver, parser/checker/codegen/runtime, CLI docs, LICENSE | Root/lifetime checking, C generation, explicit runtime boundary | Apache-2.0 at root; compiler third parties need separate review |
| [embedded-hal](https://github.com/rust-embedded/embedded-hal) | [lib.rs](https://github.com/rust-embedded/embedded-hal/blob/master/embedded-hal/src/lib.rs), [crate manifest](https://github.com/rust-embedded/embedded-hal/blob/master/embedded-hal/Cargo.toml), LICENSE-MIT | Small no_std portable peripheral contracts separate from implementation | Manifest MIT OR Apache-2.0; do not assume Goose traits |
| [esp-hal](https://github.com/esp-rs/esp-hal) | [README](https://github.com/esp-rs/esp-hal/blob/main/esp-hal/README.md), [manifest](https://github.com/esp-rs/esp-hal/blob/main/esp-hal/Cargo.toml) | Chip-specific implementations behind common contracts | Manifest MIT OR Apache-2.0; exact license files not retrieved successfully; per-file review pending |
| [Embassy](https://github.com/embassy-rs/embassy) | README, embassy-executor/Cargo.toml, LICENSE-MIT, LICENSE-APACHE | Cooperative tasks depend on language state-machine lowering; keep executor separate from HAL | Executor manifest MIT OR Apache-2.0; Goose async equivalent not established |
| [ESP-IDF](https://github.com/espressif/esp-idf) | Root LICENSE; official ESP32-S3 startup/build/memory docs | Reuse supported startup, linker and component infrastructure first | Root Apache-2.0; third-party components can have distinct licenses |

License observations only: MIT texts require retaining copyright/permission
notices; Apache-2.0 texts specify license/notice retention and modified-file
marking among their terms. Preserve relevant notices and recheck actual selected
files before redistribution; no blanket compatibility claim is made here.

Goose's [TinyCC README](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/third_party/tinycc/README.md)
identifies LGPL-2.1 plus relicensing notes, and CMake builds it into every host
compiler. Keeping compiler/toolchain downloads out of version control avoids
accidentally distributing them as this project's original implementation.
Generated standalone C includes Goose runtime code; a future distributed artifact
must account for that provenance even when users supply their own compiler.

No project LICENSE chosen in this session. This is a foundation for a public
open-source project, not yet a release with a completed distribution inventory.

The second Goose patch adapts the checked i32 helper rules from runtime.h into
canonical runtime_scalar.h (with Goose Apache-2.0 provenance in its header).
The desktop runtime itself is not copied into the new generated scalar artifact.
Both patch stages retain the upstream license and modified-file notices.

The initial target SDK is now pinned to
[ESP-IDF v6.0.2 / 7101770](https://github.com/espressif/esp-idf/tree/7101770dc6db2667b3c477cc31365dd1acd6db4e).
Inspected its LICENSE, tools.json/idf_tools.py, install/export scripts, build
actions and unchanged examples/get-started/hello_world. Root Apache-2.0;
hello_world_main.c explicitly CC0-1.0. Tool/component licenses differ, including
GPL toolchain/debug tools. SDK/tool sources and built binaries remain ignored,
not vendored. Evidence/setup: [ESP_IDF_BASELINE.md](ESP_IDF_BASELINE.md).

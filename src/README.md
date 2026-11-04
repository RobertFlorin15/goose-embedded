# Implementation boundary

The host-verified scalar-v0 compiler/runtime adaptation is maintained as pinned
upstream patches under patches/goose/. Its canonical runtime_scalar.h is inside
the second patch, separate from framework/platform/HAL implementations.
platform/esp_idf/scalar_panic.c supplies the versioned panic hook for the minimal
ESP-IDF example, with a debugger-visible source record and direct SDK abort.
It is host-stub tested and Xtensa-linked; no physical verification or HAL exists.
Follow docs/ARCHITECTURE.md and research/ESP32S3_SCALAR.md. Board configuration
belongs outside the scalar runtime; one image is not universal across modules.

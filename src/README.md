# Implementation boundary

The host-verified scalar-v0 compiler/runtime adaptation is maintained as pinned
upstream patches under patches/goose/. Its canonical runtime_scalar.h is inside
the second patch, separate from future framework/platform/HAL implementations.
No ESP-IDF platform binding or HAL is implemented here. Future portable runtime,
platforms and drivers should follow docs/ARCHITECTURE.md. Current examples and
C platform hooks are host verification inputs, not flashed firmware.

# Board variants and physical validation

The user has several ESP32-S3 board types and wants eventual support across
them. No exact board inventory has been supplied and none is physically verified.
Keep the scalar runtime independent of the module/carrier board. ESP-IDF settings
describe flash mode/size/frequency, PSRAM variant and console routing; an image
built with one set of those settings is not a universal board image. Later HAL
resource/pin mappings also belong to a platform/board layer.

## Current evidence

The scalar example builds for chip target esp32s3 at -O0/-O2. Its SDK defaults
select DIO/2 MB flash, no enabled PSRAM, and the SDK default console. These are
control-build settings only; they are not measured properties of any user board.
Do not add speculative board definitions or enable PSRAM solely from a guessed
commercial product name. No pin wiring or peripheral operations are implemented.

## Repeatable validation record, per board configuration

Before any physical operation, identify and retain:

1. Board/carrier revision and module marking; authoritative schematic/module
   documentation for flash/PSRAM type, size and relevant boot/console wiring.
2. Reviewed SDK config (chip/revision, flash mode/frequency/size, partition table,
   PSRAM mode or disabled state, console routing and RTOS stack setting).
3. Build/source/compiler/SDK identity, full sdkconfig, image/map hashes and
   configuration-specific acceptance expectations. Preserve the scalar checks
   and panic-policy guard; do not bypass them for a board variant.
4. Explicit authorization for the specific flash/serial action, port and image.
   A generic request to develop the framework does not authorize hardware use.
5. Actual boot/serial log: expected scalar result 42, no unexpected reboot, and
   stack high-water measurement with the reviewed calling workload. Fatal-case
   tests are separate firmware variants, separately reviewed before execution;
   verify overflow and lifecycle guards reach the selected halt policy.
6. Distinguish build-only, simulator, success-path physical and fatal-path physical
   status for each configuration. Record failures and supported limitations.

Start with one identified configuration to establish M2b; repeat across the user's
variants rather than assuming similar-looking boards are identical. Additional
flash/PSRAM/console configurations should use explicit SDK defaults/overlays in
separate build outputs, sharing the Goose library and C platform binding. No
board registry, driver abstraction or automatic flashing is needed yet.

Current matrix:

| Configuration | Target build | Physical success | Physical panic | Stack budget |
|---|---|---|---|---|
| ESP32-S3 scalar control, SDK defaults except reviewed panic policy | Pass -O0/-O2 | Not run | Not run | Partial static frames only |
| User board variants (identity/settings pending) | Not run | Not run | Not run | Unverified |

See [target report](../research/ESP32S3_SCALAR.md) and [roadmap](ROADMAP.md).

Measurement preparation now cross-builds and is host-double tested; actual board
readings remain absent. Use [the run template](HARDWARE_RUN_TEMPLATE.md) and
[stack audit](../research/STACK_MEASUREMENT.md). The example prints three byte
low-water samples and retains a fourth post-report sample for a debugger. Sample
differences are not isolated Goose consumption, and fill-pattern scanning does
not certify the full task budget. Normal samples do not measure a fatal workload.

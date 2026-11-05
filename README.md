# Goose Embedded

An early investigation into an embedded ecosystem for
[aardappel/Goose](https://github.com/aardappel/goose), initially targeting ESP32-S3.

**Status:** feasibility analysis, Linux scalar runtime probes, and the unchanged
official ESP-IDF ESP32-S3 baseline build pass. Scalar Goose C also links for
ESP32-S3 at -O0/-O2; hardware execution remains unverified and no HAL exists. The desktop
runtime's virtual-memory model and 64-bit reference layouts need adaptation.

Start with [the feasibility report](research/FEASIBILITY.md),
[reproducible host probes](tools/README.md), [scalar profile design](docs/SCALAR_PROFILE.md),
and [roadmap](docs/ROADMAP.md). The opt-in scalar validator and isolated runtime are host-tested;
The [scalar target report](research/ESP32S3_SCALAR.md) records the platform
adapter, dependency/ABI/stack inspection and limits. Board-specific flash/PSRAM/
console configurations need [separate validation](docs/HARDWARE_VALIDATION.md).
The [stack audit and measurement preparation](research/STACK_MEASUREMENT.md)
passes cross-build/host tests; no target readings or complete stack budget exist yet.
[Configuration inputs and offline log checks](research/CONFIGURATION_LOG_VALIDATION.md)
also pass; all automated captures are synthetic.
Agents should read [AGENTS.md](AGENTS.md), [project state](docs/PROJECT_STATE.md),
[handoff](docs/HANDOFF.md), and the [project skill](.agents/skills/goose-embedded/SKILL.md).

Research references are attributed in [REFERENCES.md](research/REFERENCES.md).
Project license selection is pending dependency/distribution review; this is
not yet a public release. Downloaded compiler sources and generated runtime
code are not tracked here.

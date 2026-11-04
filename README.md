# Goose Embedded

An early investigation into an embedded ecosystem for
[aardappel/Goose](https://github.com/aardappel/goose), initially targeting ESP32-S3.

**Status:** feasibility analysis, Linux scalar runtime probes, and the unchanged
official ESP-IDF ESP32-S3 baseline build pass. Goose target integration and
hardware execution remain unverified; no HAL is implemented. The desktop
runtime's virtual-memory model and 64-bit reference layouts need adaptation.

Start with [the feasibility report](research/FEASIBILITY.md),
[reproducible host probes](tools/README.md), [scalar profile design](docs/SCALAR_PROFILE.md),
and [roadmap](docs/ROADMAP.md). The opt-in scalar validator and isolated runtime are host-tested;
The [pinned SDK baseline](research/ESP_IDF_BASELINE.md) passes; the next step is
cross-building Goose-generated scalar C with a small platform adapter.
Agents should read [AGENTS.md](AGENTS.md), [project state](docs/PROJECT_STATE.md),
[handoff](docs/HANDOFF.md), and the [project skill](.agents/skills/goose-embedded/SKILL.md).

Research references are attributed in [REFERENCES.md](research/REFERENCES.md).
Project license selection is pending dependency/distribution review; this is
not yet a public release. Downloaded compiler sources and generated runtime
code are not tracked here.

# Roadmap

Progress labels apply only to the acceptance criteria below.

| Milestone | Acceptance criteria | State |
|---|---|---|
| M1 — feasibility analysis | Pinned source-backed compiler/runtime/memory/ABI report; reproducible host probes; blockers; minimal target plan | Complete as analysis: research/FEASIBILITY.md, EXPERIMENTS.md and host-results.json. Target feasibility remains conditional. |
| M2a — target contract and cross-build | Restricted feature contract enforced; startup/runtime adaptation; pinned ESP-IDF/toolchain; minimal generated C linked for esp32s3; map and ABI review | Complete for scalar leaf at -O0/-O2; full task stack/hardware evidence still required before execution claims |
| M2b — minimal hardware execution | Authorized known board; app_main invokes Goose; serial/measured output demonstrates expected result; firmware/source/toolchain identity and log retained | Not started; gate for M3 |
| M3 — basic peripherals | GPIO, UART, timers, PWM, ADC separately implemented and verified with board-specific wiring, error cases and measurements; bounded memory use | Blocked on M2 |
| M4 — portable HAL | Small GPIO/SPI/I2C contracts, initialization/errors/resource policy; adapters and driver contract tests; portability demonstrated or explicitly unverified | Blocked on M3 |
| M5 — advanced capabilities | Interrupt/reentrancy and concurrency safety specified/tested before robotics drivers or executor; motor/encoder tests include authorized safe setup | Blocked on runtime/HAL prerequisites |
| M6 — expansion | Additional target has reproducible build/hardware proof; debugging/HIL/docs/contribution workflow verified | Future |

M2a design checkpoint: startup/symbol inventory and scalar-v0 contract are
complete (SCALAR_PROFILE.md, research/RUNTIME_STARTUP.md). Compiler allowlist,
rejection tests, restricted lifecycle/failure and desktop regressions now pass.
Official ESP-IDF v6.0.2 control and scalar leaf builds pass with the pinned
toolchain. research/ESP32S3_SCALAR.md records ABI/map/assembly review and partial
compiler frame sums, not a whole-task stack guarantee. SDK/ROM audit and normal
task measurement preparation now pass (research/STACK_MEASUREMENT.md); no actual
readings exist. Explicit configuration inputs and offline normal-run consistency checks also pass
(research/CONFIGURATION_LOG_VALIDATION.md). Separately built success/cold-export/overflow cases and fatal saved-log checks
also pass six target builds and host/synthetic tests (research/FATAL_CASES.md).
Fatal SDK/exception ownership and individual-frame audit is documented in
research/FATAL_STACK_AUDIT.md; complete stack requirements remain open. Next
independent task: pinned dependency/tool license inventory before choosing a
project license. Per-board execution remains gated (HARDWARE_VALIDATION.md). User has multiple board variants; no exact
board configuration is identified and no hardware action is authorized.
Do not start unbounded arenas, HAL or an async framework as a shortcut around the runtime gate.

Automatic model orchestration is a possible future tooling improvement, outside
initial milestones. Sol handles routine setup/implementation; checkpoint and
recommend Astra where ABI/memory safety design merits deeper review.

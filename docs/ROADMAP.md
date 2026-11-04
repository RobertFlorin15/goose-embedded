# Roadmap

Progress labels apply only to the acceptance criteria below.

| Milestone | Acceptance criteria | State |
|---|---|---|
| M1 — feasibility analysis | Pinned source-backed compiler/runtime/memory/ABI report; reproducible host probes; blockers; minimal target plan | Complete as analysis: research/FEASIBILITY.md, EXPERIMENTS.md and host-results.json. Target feasibility remains conditional. |
| M2a — target contract and cross-build | Restricted feature contract enforced; startup/runtime adaptation; pinned ESP-IDF/toolchain; minimal generated C linked for esp32s3; map and ABI review | Not started |
| M2b — minimal hardware execution | Authorized known board; app_main invokes Goose; serial/measured output demonstrates expected result; firmware/source/toolchain identity and log retained | Not started; gate for M3 |
| M3 — basic peripherals | GPIO, UART, timers, PWM, ADC separately implemented and verified with board-specific wiring, error cases and measurements; bounded memory use | Blocked on M2 |
| M4 — portable HAL | Small GPIO/SPI/I2C contracts, initialization/errors/resource policy; adapters and driver contract tests; portability demonstrated or explicitly unverified | Blocked on M3 |
| M5 — advanced capabilities | Interrupt/reentrancy and concurrency safety specified/tested before robotics drivers or executor; motor/encoder tests include authorized safe setup | Blocked on runtime/HAL prerequisites |
| M6 — expansion | Additional target has reproducible build/hardware proof; debugging/HIL/docs/contribution workflow verified | Future |

Immediate M2a design sequence: inventory zero-region runtime initialization and
required symbols; specify opt-in restricted profile and rejection rules; test
host lifecycle/rejections; pin target toolchain and run official baseline build;
then integrate generated leaf library. Do not start unbounded arenas, HAL or an
async framework as a shortcut around the runtime gate.

Automatic model orchestration is a possible future tooling improvement, outside
initial milestones. Sol handles routine setup/implementation; checkpoint and
recommend Astra where ABI/memory safety design merits deeper review.

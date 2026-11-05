# Handoff

2026-11-05. **Configuration/normal-run tooling verified on target builds and
synthetic captures only. No physical/simulator execution or full stack bound.**

Recover AGENTS.md -> PROJECT_STATE.md -> project skill -> Git/source/evidence.
Branch main, no remote. Prior stack checkpoint 04b4b5aed7615ff3ea95d3eb5a28ba769cb34417.
Current checkpoint is the commit containing this handoff (git log -1 resolves it).
Task changes intended to be committed together; verify status. Unrelated untracked
.vscode/ appeared during work and is untouched/excluded from this checkpoint. SDK and Goose reference
trees remain clean; compiler/runtime patches and SDK panic binding unchanged.
M2a leaf cross-build gate passes, M2b unverified and HAL blocked.

New: ordered --defaults overlays with required --config-id, snapshots of input
bytes/.esp32s3 siblings, mutation/unknown-symbol/effective policy checks, per-level
run manifests. Full ELF identity from SDK image descriptor now prints first;
esptool verifies image fingerprint. Completion marker prints after fourth sample.
Identity printing influences lifetime low-water readings; completion print and
SDK return/deletion remain outside measurements. App frame stays 48 bytes.

Offline tools/validate_scalar_run.py checks saved artifacts/capture/log only.
Success means consistent, always hardware_execution_proven=false and
stack_bound_proven=false. Actual logs do not exist. Every automated capture is
synthetic, including four using real build fingerprints. Parser tests declaring
physical type prove that a declaration never authenticates execution. Missing
numeric debugger after_report remains null; partial/stale records rejected.
No arbitrary safe threshold; zero data flagged. Hash/parse same bytes, bounded
logs, relative-path/symlink/duplicate-key checks. See docs/RUN_LOG_FORMAT.md.

Verified:
- 28 unittest cases plus table subcases, no SDK/hardware dependencies.
- Control + test-4mb probes, each 75 commands /18 expected failures: four firmware
  builds O0/O2 with all existing bridge/ABI/units/arithmetic/dependency checks.
- Effective control 2 MB/3584 stack; fixture 4 MB/4096 from target sibling. Fixture
  is not a physical board definition. Images 146144/O0,145824/O2 bytes each config;
  hashes differ. Full ELF digest in image matches linked ELF for all four.
- Six supplementary strict application-host compile/run checks pass at final
  source revision (O0/O2).
- Four synthetic normal captures validate against actual manifests; wrong one
  rejected. Two actual SDK bad-policy/unknown-symbol configurations fail before
  build and publish no manifest. Five known generated unused warnings per level;
  no new app warning/suppression. SDK/Goose trees clean.

Commands:
```sh
python3 -m unittest discover -s tests -p test_scalar_tools.py -v
python3 tools/test_esp_idf_scalar.py --output build/new-control
python3 tools/test_esp_idf_scalar.py --config-id my-config --defaults /path/to/reviewed.defaults --output build/new-config
python3 tools/validate_scalar_run.py --manifest build/new-config/O0/run-manifest.json --capture /path/to/capture.json
```
Fresh output required. Original test output build/esp-idf-config-{control,overlay,
bad-policy,unknown}; unit/synthetic CLI logs build/config-fixtures. Reproduction
and reviewed summary in research/CONFIGURATION_LOG_VALIDATION.md and linked JSON.
Tracked tests/esp_idf/configs contain only build/refusal fixtures. Manifests need
adjacent original artifact layout; defaults snapshot paths are relative to probe
root. Referenced CSV/env inputs still need separate provenance review.

User has several ESP32-S3 types and wants future coverage across them. No exact
inventory, reviewed physical configuration or hardware authorization supplied.
Do not turn test fixtures into board presets or repeatedly ask for one board as
if it defines the framework. No actual sample or result-42 observation; full task/
ROM/callback/exception/window stack reasoning remains open. Scope is normal task,
caches enabled, serial callers; no ISR/concurrency/HAL.

Next: separately select fatal firmware cases (e.g. overflow/cold export) and
validate expected diagnostics independently of normal-run checks, with target/
host rejection tests and per-case manifests. Build/test only; no physical action.
Sol/medium suits routine case tooling; Astra/high for stack/exception proof.
Before flash/serial/debug: identify/review exact module/config and obtain explicit
hardware authorization. License inventory/full upstream suites remain pending;
Grapify unavailable in prior checks, standard tools used. Pins/setup unchanged in
tools/README.md (.cache/goose-scalar-runtime and .cache/esp-idf-v6.0.2).

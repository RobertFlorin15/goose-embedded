# Goose Embedded: agent instructions

## Mission and scope
Determine whether aardappel/Goose can run on ESP32-S3, then progressively build a portable embedded ecosystem. Verify feasibility before HAL work. Learn from Rust Embedded; do not assume Goose has ownership, borrowing, traits, or async support.

## Recovery (every session)
1. Read this file, docs/PROJECT_STATE.md, docs/HANDOFF.md, and .agents/skills/goose-embedded/SKILL.md.
2. Inspect `git status --short --branch`, `git log -5 --oneline`, and relevant source.
3. Reconcile documentation with actual files/results; identify the latest verified milestone.
4. Continue the exact next task. Never infer hardware success from a build.

## Structure
- docs/: durable state, handoff, roadmap, architecture, decisions, learning notes.
- research/: pinned upstream evidence and feasibility reports.
- tools/: reproducible host/build probes; tests/: project verification.
- src/: future runtime/platform/HAL implementation; examples/: application inputs.
- .agents/skills/goose-embedded/: reusable project method; progress belongs in docs/.
- .cache/ and build/: ignored downloaded sources and generated artifacts.

## Workflow and standards
Investigate, define acceptance criteria, make the smallest reversible change, compile/test, inspect results, update memory, and commit coherent work. Use source permalinks and revision pins for upstream claims. Keep compiler adaptations separate from runtime, platforms, HAL, and drivers. Do not vendor external code without its license. Project license is pending dependency review.

Commands: `python3 tools/host_probe.py --compiler /path/to/pinned/goose`; read tools/README.md for pinned setup and experiment semantics. Pinned official ESP32-S3 control build: `python3 tools/esp_idf_baseline.py --output build/esp-idf-baseline-new` (requires SDK setup in tools/README.md and a fresh output). Scalar leaf cross-build/host bridge checks: `python3 tools/test_esp_idf_scalar.py --output build/esp-idf-scalar-new` (same pinned setup, fresh output). Physical execution and whole-task stack budget remain unverified; board variants need separate settings/evidence. Host probe success is host evidence only.

After significant work update PROJECT_STATE and HANDOFF, record exact commands/results and unresolved failures, and update architecture/decisions/learning notes where relevant. A commit cannot contain its own hash: state documents may identify their containing commit with `git rev-parse HEAD`, and must clearly label prior explicit hashes.

## Safety
No destructive Git actions, force pushes, separately billed APIs, or unsafe hardware operations without explicit authorization. Do not flash or drive hardware until authorized. No invented registers, test results, or portability claims. Stop retries when no new hypothesis exists. Do not implement orchestration infrastructure during initial milestones.

## Models and handoff
Sol is the routine default. Recommend Astra for runtime/ABI/memory/interrupt questions with a specific technical reason; checkpoint before transitions. Do not assume in-session model switching. Keep docs cross-agent compatible; record branch, commit semantics, dirty state, blockers, and exact next commands. Grapify is optional: verify its installation and read its instructions before use; otherwise document standard-tool fallback.

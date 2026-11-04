---
name: goose-embedded
description: Investigate, implement, test, and hand off Goose Embedded compiler adaptations, runtime, and ESP32-S3 integration in this repository.
---

# Goose Embedded

Build a source-backed path from aardappel/Goose-generated C to ESP32-S3, then a portable embedded ecosystem. Read repository AGENTS.md first. Treat Goose's verified features as the design boundary; Rust projects supply principles, not an API to translate.

## Recover and scope
At each session start read docs/PROJECT_STATE.md and docs/HANDOFF.md, inspect Git status/history and relevant implementation, and reconcile discrepancies. Read docs/ARCHITECTURE.md and research/FEASIBILITY.md before compiler/runtime work. Current progress belongs in state/handoff, not this skill.

## Method
Define acceptance criteria, inspect pinned upstream source, choose the smallest reversible experiment/change, compile and test, analyze failures, review, checkpoint, and commit coherent changes. Cite exact upstream revisions and source locations. Verify Grapify is installed and read its SKILL.md before invoking it; if absent, record the limitation and use standard source tools.

Keep host compiler changes, target runtime, platform bindings, portable HAL, peripheral drivers, and applications separate. Preserve Goose's memory/lifetime guarantees: a smaller arena cannot replace guarded virtual memory without checks before every relevant write or a proven restricted subset. Audit target pointer widths, packed alignment, C ABI, startup and teardown. Do not assume desktop runtime, threads, or allocation-free marketing claims imply embedded compatibility.

## Verify
Use tools/README.md for reproducible setup and tools/host_probe.py for host evidence. Pin dependencies and retain logs/revision/tool versions. Label static inspection, host execution, target compilation, simulator execution, and physical hardware execution separately. No HAL before feasibility prerequisites; no interrupt/concurrency layer before runtime safety is established. Never invent registers or evidence. Follow AGENTS.md hardware, Git, network/cost authorization constraints.

## Persistent memory and handoff
After significant engineering work update PROJECT_STATE and HANDOFF with verified results, exact commands, failures, dirty files, branch/commit, blockers and next action. Record architectural decisions in docs/DECISIONS.md and reusable explanations in docs/LEARNING_NOTES.md. A handoff must be usable without chat history. Before a model transition checkpoint; recommend Sol for routine tasks and Astra for material ABI, memory-safety, interrupt or concurrency design questions. Do not build a model router.

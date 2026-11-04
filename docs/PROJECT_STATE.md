# Project state

Updated 2026-11-04. Authoritative evidence: research/FEASIBILITY.md,
EXPERIMENTS.md, host-results.json, upstream.json; regenerate via tools/README.md.

## Current milestone and task

M1 **complete as feasibility analysis**: pinned compiler architecture, runtime,
memory/ABI investigation, host experiments, blockers and minimal plan delivered.
Embedded feasibility is conditional, not proven. M2 has not started.
Current task: M1 checkpoint committed; next design zero-region target profile.

## Completed

- Inspected empty workspace; initialized Git main.
- Established AGENTS.md, reusable project skill, roadmap, architecture, decisions,
  learning notes and resumable state/handoff.
- Grapify installation/tool check: unavailable in inspected roots and tool catalog;
  used standard source inspection, no Grapify commands executed.
- Pinned/downloaded official Goose 335fddc13dc74666398ffe160ec8a8f2958329d0;
  clean ignored copy at .cache/goose; host build at /tmp/goose-build.
- Built Release compiler, verified scalar/growth C emission/execution, C export
  lifecycle/restart with and without Goose main, 32-bit layout witness.
- Reviewed requested ecosystem references and preliminary license inventory.

## Verified technical discoveries

- Typed/specialized AST -> optimization/BCE -> C; host compiler C++20/TinyCC.
- Desktop runtime uses VM regions, protection/fault handlers, and C heap metadata.
- Codegen hard-codes reference/slice sizes for 64-bit layouts; -m32 witness shows
  packed C layouts differ. Actual target miscompilation not yet reproduced.
- Leaf scalar export reports zero regions but still enters desktop gs_rt_init.
- C export/lifecycle path works on Linux x86-64, including two restarts.

## Incomplete and blockers

- No restricted target profile/enforcement or runtime adaptation implemented.
- No target C compilation, ELF/map/assembly review, simulator or physical run.
- idf.py and xtensa-esp32s3-elf-gcc absent from PATH; no SDK version selected.
- No board/serial setup identified; hardware operations require authorization.
- Packed alignment, 32-bit layout, memory safety and error lifecycle remain open.
- Upstream build warnings recorded in EXPERIMENTS.md; full upstream suite not run.
- Project license/distribution inventory incomplete; not release-ready.

## Files modified

All tracked foundation files were introduced this session: AGENTS.md, .gitignore,
README.md, .agents/skills/goose-embedded/SKILL.md, docs/*.md,
research/{FEASIBILITY,EXPERIMENTS,REFERENCES}.md, upstream.json, host-results.json,
tools/{host_probe.py,README.md}, examples/{scalar,growth,leaf}.goose,
tests/{c_host,layout_witness}.c, src/README.md. Build/cache are ignored.

## Verification

- CMake configure and Release build: exit 0 (23 build steps), with upstream warnings.
- `python3 tools/host_probe.py --compiler /tmp/goose-build/goose`: PASS, 19 commands.
- Skill quick_validate.py: PASS.
- Local Markdown link existence check: PASS; archived JSON has 19 exit-0 records.
- Staged Git whitespace check: PASS; foundation commit created and clean status verified.
- Target compilation / simulator / physical hardware: NOT RUN.

## Git and next action

Latest verified implementation commit: `a5d7f672a90a73ce92c30d2eb9d6f45af180dc1c`
(M1 foundation, including all 19 passing command records). This file is updated
in a subsequent documentation checkpoint; resolve that checkpoint with
`git rev-parse HEAD`. Branch main; no remote configured. Working tree was clean
after the foundation commit; this checkpoint updates only state/handoff and is
intended to leave no uncommitted changes. Always verify with git status.

Next actionable task: inventory initialization and required symbols of
examples/leaf.goose in separate-runtime mode; design an opt-in zero-region target
profile with explicit feature rejection and lifecycle tests before implementation.
Recommend Astra/high for runtime safety/ABI design per project model strategy;
Sol/medium for subsequent routine implementation/toolchain setup. No automatic
model switching or paid API usage occurred.

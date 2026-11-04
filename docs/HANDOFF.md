# Handoff

2026-11-04. Objective: move from completed M1 analysis to a safe minimal ESP32-S3
cross-build; no HAL yet. Read AGENTS.md, PROJECT_STATE.md and the project skill.

Last verified result: Release Goose host compiler built; 19 probe commands pass,
including scalar/growth apps, C-host lifecycle/restart, zero-region scalar leaf
and 32-bit packed-layout witness. Skill syntax and local doc links pass.
No Xtensa compile, simulator or hardware execution. No flash/hardware operation.

Git: main; M1 foundation is the commit containing this handoff (resolve with
`git log -1 --oneline`). No pre-existing user changes or configured remote.
All foundation changes are intended to be committed; verify `git status --short`
when resuming. Ignored .cache/goose, build/host-probe and /tmp/goose-build are
local conveniences, not portable prerequisites; tracked logs survive cache loss.

Discoveries: desktop VM-backed stacks and C heap metadata; hard-coded 64-bit
reference/slice layouts; leaf exports report zero regions but still run desktop
startup; --header provides C exports and goose_init/goose_exit. Grapify absent.
Evidence and source permalinks: [feasibility](../research/FEASIBILITY.md),
[experiments](../research/EXPERIMENTS.md), [architecture](ARCHITECTURE.md).

Blockers: no pinned ESP-IDF/toolchain installed for this project; no board details;
profile/runtime/32-bit ABI not adapted; license inventory not release-complete.

Exact next steps:
1. Inspect leaf output with separate runtime emission; enumerate init/exit and
   export dependencies, especially zero-region allocations/OS setup.
2. Specify opt-in restricted profile, feature rejection and lifecycle checks.
   Checkpoint design before edits. Recommend Astra/high for this safety/ABI step;
   no model switching mechanism is assumed.
3. Implement smallest reviewed adaptation with host/rejection tests, then pin
   official ESP-IDF/toolchain and prove its baseline build before Goose integration.
4. Only after target build and authorized board operations, verify serial result 42.

Commands:
```sh
git status --short --branch
git log -5 --oneline
python3 tools/host_probe.py --compiler /tmp/goose-build/goose
# If temporary compiler is gone, use the build commands in tools/README.md.
```

[Roadmap](ROADMAP.md) has acceptance gates; [decisions](DECISIONS.md) constrains
memory safety; [learning notes](LEARNING_NOTES.md) explains the concepts.

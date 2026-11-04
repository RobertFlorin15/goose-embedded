# Handoff

2026-11-04. M1 analysis is complete; M2a design/probing is in progress.
Current result: separate-runtime startup inventoried; scalar-v0 contract written.
**No target profile/runtime adaptation, Xtensa build, HAL or hardware run exists.**

Recovery: AGENTS.md -> PROJECT_STATE.md -> project SKILL.md -> Git/source check.
Git branch main; previous verified checkpoint 757a6d8; M1 foundation a5d7f67.
This design/probe checkpoint is the commit containing this handoff: get exact ID
with `git log -1 --oneline`. Clean on recovery; task changes are intended to be
committed together, leaving no uncommitted changes. Check `git status --short`.
No remote; ignored caches/generated files are disposable, not source history.

Last verification: new runtime_probe.py PASS, 32 commands at Goose/native -O0
and -O2; six expected failures (pre-init, post-exit, checked overflow at each
level) and remaining exit-0 commands. C observer/host are warning-free under
-Wall -Wextra -Werror syntax checks. Archived logs and doc links checked.
Earlier M1 19-command probe passed; not rerun since no baseline source changed.

Discoveries: zero-region init still allocates metadata and signal stack, installs
signals and queries native stack; separate runtime shutdown uses pthread locking.
Successful scalar export and idempotent calls are quiet for selected wrapped
APIs. Zero regions do not exclude foreign calls, references or recursion;
GS_MAX_STACKS=0 disables the limit. Full evidence/limits:
[research/RUNTIME_STARTUP.md](../research/RUNTIME_STARTUP.md).

Exact next steps:
1. Read [SCALAR_PROFILE.md](SCALAR_PROFILE.md) and decision 005. Add a tracked
   upstream patch (not an undocumented cache edit) implementing the proposed
   opt-in scalar-v0 mode and structural/type validation before optimization.
2. Add rejection tests including uncalled and dead unsupported code, both -O0
   and -O2; keep normal desktop behavior unchanged. Checkpoint that change.
3. Separately adapt inline init/generated exit and the panic boundary. Replacing
   only gs_rt_start misses inline calloc/free. Test no selected allocator/VM/
   signal/pthread calls, lifecycle guards and arithmetic failures.
4. Only then pin official ESP-IDF/toolchain and establish its baseline build,
   then compile the generated leaf component. Board/flash work needs explicit
   authorization and recorded board details; no hardware operation authorized.

Blockers: profile not implemented; no target SDK selected; 32-bit layouts and
alignment unverified beyond scalar hypothesis; no target stack budget or board;
license/distribution inventory incomplete. Grapify unavailable in prior check.
Recommend Astra/high for next validation/safety implementation; no automatic
model switch is assumed.

Commands (from project root):
```sh
git status --short --branch
git log -3 --oneline
git -C .cache/goose rev-parse HEAD
git -C .cache/goose status --short
python3 tools/runtime_probe.py --compiler /tmp/goose-build/goose
```
Source must be clean pin 335fddc13dc74666398ffe160ec8a8f2958329d0. Compiler
currently reports runtime d22ae129d92b. Rebuild if /tmp compiler disappears via
[tools/README.md](../tools/README.md). Tracked runtime-results.json and
runtime-summary.json preserve evidence if caches disappear. See
[roadmap](ROADMAP.md), [architecture](ARCHITECTURE.md), [learning notes](LEARNING_NOTES.md).

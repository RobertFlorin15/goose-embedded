# Decision log

## 001 — Host AOT compiler, ESP-IDF target integration (2026-11-04)

Problem: reach ESP32-S3 without porting development tools to the chip.
Alternatives: port compiler/TinyCC, write machine-code backend, generate C and
reuse ESP-IDF. Selected: investigate host-generated C with ESP-IDF. Rationale:
upstream C emission and export lifecycle exist and work on host; IDF supplies
startup/linking. Tradeoff: runtime and ABI portability remain our work; using C
is not a target compatibility proof. Consequence: no on-device compiler/JIT.

## 002 — Prove a restricted scalar subset first

Problem: guarded VM growth and hard-coded 64-bit pointer sizes block a full
runtime port. Alternatives: small unchecked static arenas; full runtime rewrite;
restricted zero-region profile then incremental safe expansion. Selected:
design the restricted profile first. Evidence: leaf export reports zero regions,
but still calls runtime init. Rationale: minimizes initial semantics and exposes
startup obstacles. Tradeoff: no useful dynamic data or HAL yet. Consequence:
profile enforcement, lifecycle adaptation and target compiler validation must
precede any claim of support. Exact enforcement design is next work, not done.

## 003 — Preserve safety when bounding memory

Problem: desktop growth can bump pointers with no per-write arena check.
Alternatives: rely on MCU faults/canaries; insert checks; statically forbid
unproven growth. Selected constraint: before supporting data stacks, check every
relevant write before it occurs or prove sufficient capacity for that subset.
Rationale: after-write canaries and guessed guard behavior cannot preserve
memory safety. Tradeoff: performance/implementation cost; checks require overflow-
safe arithmetic. Consequence: no static-buffer drop-in runtime replacement.

## 004 — Pinned evidence; license decision deferred

Problem: moving upstream and compiler third parties obscure reproducibility
and redistribution obligations. Selected: pin Goose, keep downloads/generated
C ignored, record source links and license observations; defer project license
until concrete dependency/distribution review. Alternative: vendor compiler or
pick a license from the root README alone. Tradeoff: not ready for public release
yet. Consequence: preserve attribution when future code is copied/distributed.

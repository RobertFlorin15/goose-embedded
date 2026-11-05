# Learning notes

## C output is a portability boundary, not a portability guarantee

A compiler can translate `i32` addition into a C expression without knowing
Xtensa instructions. The target C compiler selects those instructions. But C
that invokes mmap or assumes eight-byte pointers still encodes host assumptions.
Our host leaf export proves the translation/export path, not MCU startup.

## Typed specialization bodies are an intermediate representation

An IR need not be LLVM or SSA. Goose checks generic functions into FnSpec bodies,
optimizes their AST nodes and emits C from them. To add a memory check, locate
the actual construction/store lowering rather than invent a new compiler stage.
See src/codegen_construct.h and codegen_emit.h at the recorded upstream pin.

## ABI means agreement about values and calls

A C caller and Goose export must agree on argument types, layout, alignment,
register/stack passing and lifecycle. Internal hidden stack arguments do not
belong to public exports. Upstream assumes slices take 16 bytes; packed pointer
plus i64 on a 32-bit C model takes 12. Both sides compiling successfully can
still disagree about an aggregate's offsets. Scalar-only first tests reduce
that surface; later tests must cover aggregate fields and callbacks explicitly.

## A data stack differs from the native call stack

Native stack holds C call frames. Goose data stacks hold inline variable-size
values (and some large fixed values), with compiler-controlled top pointers.
Scope exit can restore a top in constant time. The number of simultaneous data
stacks is not the bytes they consume, nor the C stack depth. Our growing array
example reports two regions; that does not mean it physically consumes 4 GiB.

## Virtual reservation versus committed RAM

Linux can reserve a large address range and back only touched pages. Goose uses
that behavior with a protected tail. ESP32-S3 has memory mapping for flash/cache,
but that is not evidence for POSIX anonymous VM and signal handling. A 4 KiB
static arena must reject a 4097th byte *before* writing it, including overflow
checks on lengths and pointer arithmetic. A canary checked afterward is too late.

## “No heap” needs a scope

Goose values need no general-purpose heap allocator, but current C runtime
startup allocates stack metadata with calloc even at zero data stacks. Error and
thread paths allocate too. An embedded memory claim must include metadata,
startup, error handling, SDK allocations and RTOS task stacks, not just values.

## Build proof, hardware proof, interrupt proof

A host test establishes host behavior. An Xtensa ELF establishes target compile/
link success. Serial output from a recorded firmware/board establishes a physical
execution observation. None establishes ISR safety: interrupts can interrupt
runtime mutation, and IRAM-safe handlers have code/data placement restrictions.
Keep first execution in app_main's normal task context and investigate interrupts
as a separate contract.

## A configuration value of zero can mean “unlimited”

The name GS_MAX_STACKS sounds suitable for setting a zero-stack requirement.
But upstream CheckStackLimit uses `maxstacks > 0 && stacks > maxstacks`; zero
turns that check off. Our growth fixture still reports two regions under that
flag. Read boundary-value semantics in the implementation before using a flag
as a safety gate. Even a real zero count would not exclude native recursion.

## Static symbols and executed calls answer different questions

`nm -u leaf.o` lists symbols an object needs resolved, including unused static
helpers at -O0. Section garbage collection can discard some at link time.
A link-time --wrap observer instead counts selected calls that run during init,
export and exit. Our leaf export calls none of those selected functions on
success; its initializer still calls calloc twice and installs signal handlers.
Neither technique alone proves a language subset: an arbitrary C extern might
have an innocuous name while doing unsafe work. Use source/type validation,
link evidence and execution observations together, each with a stated scope.

## Cold and ready are a lifecycle contract

Before goose_init, calling an export fails; repeat init while ready is a no-op;
exit restores cold, after which init can restart it. Those states need not require
allocation. The target adaptation should preserve these observable transitions
while replacing desktop setup, and preserve arithmetic failure through a
platform panic hook. Tests must cover invalid transitions as well as result 42.

## Validate before a transformation can erase evidence

An optimizer may discard `if false { print("hidden"); }`. A target profile that
forbids I/O must still reject that source when selected. Our first walk visits
all parsed function bodies, including unused code; the second checks resolved
specializations before optimization. A third check verifies backend stack/state
invariants. Each stage establishes a different fact; none is replaced by a regex
or a successful linker run.

## Typechecking can transform an AST too

Goose checks `return 1 + 2` into a representable literal before its Optimizer
runs. Adaptable integer literals may carry an i64 annotation even when they are
used as i32 constants. Rejecting every such annotation would reject valid scalar
code. The validator distinguishes these constants from stored or runtime values,
whose concrete types must be i32/bool. The tests also reject inferred i64 locals,
including inside dead branches.

## API compatibility matters inside a compiler

ParseProgram is declared by the language-server code as well as defined in the
driver. Adding a defaulted parameter only to the definition created an ambiguous
overload for existing calls. Keeping that signature and adding a default-off
policy field to its existing Ast argument preserves those callers. Scoped CLI
and diagnostic regression tests verify ordinary behavior after the patch.


## An isolated runtime needs an explicit failure boundary

The scalar object no longer needs mmap, calloc, signal or thread startup; it
needs exactly ge_scalar_v0_panic_v1 on the tested builds. This required symbol
is deliberate: the platform must define what a fatal failure means. Our Linux
hook writes a diagnostic and exits. ESP-IDF must get its own reviewed binding;
a default no-op panic would violate overflow/initialization safety.

## Widen before checking a narrow operation

For i32 multiplication, computing in i32 can overflow before a later test.
The runtime computes `(int64_t)a * (int64_t)b`, checks INT32_MIN/MAX, then narrows.
The largest magnitude product is 2^62, which fits int64_t. The same principle
covers add/sub/negation. Boundary pairs and seeded cases matched Python's
arbitrary-precision results or expected overflow at both optimization levels.
This preserves the upstream checked narrow-integer rules without its full OS
runtime. On a 32-bit target the C compiler may need libgcc helpers; that is a
separate symbol/ABI question from introducing a Goose heap allocator.

## Freestanding compilation is another evidence level

Clang compiled the scalar libraries for generic i386 using only compiler headers,
with only the panic hook unresolved. That demonstrates 32-bit freestanding C
compilation for these scalar inputs. It does not verify Xtensa instruction
selection, ESP-IDF linking, memory placement or hardware behavior. Never promote
a host architecture check into a microcontroller execution claim.

## A control build separates environment failures from integration failures

Before adding Goose, compile ESP-IDF's unchanged hello_world for ESP32-S3. If
that fails, the SDK, Python dependencies or build tools need attention before
the Goose runtime is involved. Once it links, adding the scalar component gives
us a small, attributable change to inspect. Keeping the control source unchanged
and hashing it makes that comparison reviewable.

The build produces an ELF (sections, addresses and symbols), a map (what the
linker placed and retained), and flash images. These are evidence that a target
program linked. They do not show that a board booted, serial output was observed,
or an RTOS task has enough stack for Goose. Compilation and execution are
separate verification levels.

## A source commit is only one layer of a build pin

ESP-IDF gitlinks select submodule commits; tools.json selects tool archives with
hashes. Python packages come from a separately downloaded constraints file and
can change without an SDK commit change. Record installed versions and the
constraints digest as well as the SDK/toolchain. Host Python, CMake, Ninja and
configuration also affect a build. These records support reproducing an
experiment; deterministic binary identity requires additional controls such as
paths, timestamps and compiler settings.

## C ABI checks need compiler evidence as well as matching names

The generated ge_add takes two byte-aligned gs_i32 aliases and returns gs_i32.
app_main checks that its function pointer type is compatible with an int32_t
signature. Xtensa assembly then shows scalar register arguments, a normal
windowed call/return, and natural aligned stack spills; there is no hidden Goose
data-stack argument at that boundary. This checks the leaf's public ABI, not
packed aggregate/reference layout or arbitrary unaligned memory access.

## Static frame sizes are not a whole-task stack budget

The leaf's normal call-path frame sum is 224 bytes at -O0 and 80 at -O2. Those
compiler numbers omit other paths: SDK task entry, ROM console, exception and
panic diagnostics, interrupt/register-window behavior. A 3584-byte configured
task stack is not proven safe merely because a partial sum is smaller. Keep the
partial report, audit the missing paths and measure high-water use during actual
board tests. Host panic tests only check forwarding to a terminating SDK double;
they never execute Xtensa exceptions or prove a physical halt.

## Chip target and board configuration are different boundaries

Several boards can share an ESP32-S3 while differing in flash bus mode, PSRAM,
console wiring and pin availability. The scalar Goose library can stay unchanged
while ESP-IDF configurations vary. Build and validate each configuration; do not
describe one default DIO/2 MB image as supporting every module. That separation
also leaves a clear place for board pin mappings once HAL work is justified.

## High-water observations are not live stack pointers or proofs

ESP-IDF's Xtensa stack scanner counts bytes still equal to the initial fill
pattern. It reports the minimum untouched area over the task's lifetime, which
includes SDK startup, logging and our observation calls. A function can reserve
a frame without touching every byte; pattern scanning can miss that reservation.
Subtracting readings therefore does not isolate Goose cost or prove a bound.

Our example samples after result printing and again after printing the stack
report. Only the first three readings are printed; the fourth stays in a debugger
record so reporting does not silently exclude its own cost. completed marks valid
fields. The pinned API uses bytes and StackType_t is uint8_t; never assume the
word units described by generic FreeRTOS documentation apply to this port.

## Hash correlation is different from evidence authenticity

The application now prints its full ELF hash from the SDK image descriptor.
Our probe checks that the image contains the expected digest; the saved-run
validator matches it to local ELF/config/image hashes and the capture record.
This catches stale firmware selections and accidental edits. Someone can still
edit a log and its hashes together, so consistency cannot prove physical
execution, authorization or the actual module's identity. Synthetic tests stay
labeled synthetic even when their fingerprints come from real target builds.

Defaults files are requested settings; the generated sdkconfig records what the
SDK actually selected. Copying ordered defaults and target-specific siblings
prevents later file changes from silently altering the selected inputs. Inspect
the effective config and referenced dependencies too; a defaults hash alone is
not a complete, hermetic build recipe or a claim of board compatibility.

## Testing a fatal path without confusing evidence levels

A fatal operation should not return. Here cold-export calls ge_add before init;
overflow calls ge_add(INT32_MAX,1) after init. Both reach the same runtime hook,
but their message and source record distinguish the cause. A returning operation
must emit a different failure, otherwise a broken check could pass its own test.

Host tests execute actual generated code and the real C adapter, replacing only
SDK services with doubles that verify parameters and terminate the process. This
proves application/runtime/adapter sequencing on the host. Linking the same source
against Xtensa SDK proves target compatibility. Neither executes the hardware
panic handler. Synthetic logs test the offline parser only.

The SDK prints CPU halted before calling its final halt routine. Observing that
text would therefore show progress toward halt, not proof the CPU stopped or
stayed stopped. Artifact hashes correlate supplied files; they cannot turn a
synthetic or edited log into physical evidence. Keep each claim at its tested
level, and retain a separate case/configuration/ELF record for every experiment.

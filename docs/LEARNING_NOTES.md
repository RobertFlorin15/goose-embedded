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

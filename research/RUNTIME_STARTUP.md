# Separate-runtime startup investigation

2026-11-04; Linux x86-64 host only. Goose pin:
335fddc13dc74666398ffe160ec8a8f2958329d0, runtime d22ae129d92b.
No upstream source modifications, target build, simulator or hardware access.
Design outcome: [scalar-v0 profile](../docs/SCALAR_PROFILE.md), not implemented.

## Reproduce

```sh
python3 tools/runtime_probe.py --compiler /tmp/goose-build/goose
```

Use tools/README.md to rebuild the compiler if /tmp is gone. Requires a Linux
host, GCC-compatible C compiler, GNU linker --wrap/--gc-sections and GNU nm.
The script runs **32 commands**, expects exit 1 from six deliberate runtime
failure cases, and captures all statuses/stdout/stderr. Goose and C both use
-O0 or -O2; generated program uses GS_DEBUG=1; the emitted separate runtime
serves both checked and unchecked programs. No LTO. Compiler version and flags
are in [runtime-results.json](runtime-results.json); phase counts and symbol
inventories are in [runtime-summary.json](runtime-summary.json).

## Call graph: library startup and teardown

At this pin, [EmitProgramInit](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/codegen_emit.h#L973)
emits a guard and unconditional runtime init, even for zero regions:

```text
goose_init(0, NULL)
  gs_program_init                 [skip if already initialized]
    gs_rt_init(0, NULL, 0, 0, 0)   [static inline-runtime path]
      gs_rt_start_<runtime hash>   [separate runtime object]
        gs_os_page_size           -> sysconf
        setvbuf
        gs_regions_init           -> sysconf, install SIGSEGV/SIGBUS handlers
        gs_regions_begin(0)       -> calloc(one region metadata slot)
        gs_native_stack_init      -> sigaltstack, malloc (if no alternate stack),
                                     pthread stack queries
        gs_scan_init              -> host scan capability initialization
      gs_stack_block(0)           -> calloc(one gs_stack slot); loop is empty
    set synthetic globals pointer; gs_init_globals; mark initialized
ge_add(a, b)
  initialization guard            -> gs_panic if cold
  generated i32 arithmetic        -> gs_ovf on checked overflow
goose_exit                        [skip if already cold]
  gs_rt_stop
    thread bookkeeping cleanup    -> pthread mutex and frees (separate runtime)
    gs_rt_release
      gs_release_regions          -> free metadata; free alternate signal stack
      gs_fault_uninstall          -> restore previous signal handlers
      clear runtime arguments
  free(gs_stks); clear stack pointer/count; mark cold
```

Source for inline allocation: [runtime.h:1028](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/runtime/runtime.h#L1028).
Source for registry/OS/startup: [runtime_impl.h:286](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/runtime/runtime_impl.h#L286),
[487–565](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/runtime/runtime_impl.h#L487),
[1480–1541](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/runtime/runtime_impl.h#L1480).
Shutdown: [runtime_threads.h:456](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/runtime/runtime_threads.h#L456).
The separate emitted runtime sets GS_NEED_THREADS=1 and GS_RUNTIME_OBJECT=1,
even when the generated leaf program has no workers. Do not equate no workers
with no pthread runtime dependencies.

## Dynamic trace

A link-time observer counts direct calls from linked code to 14 selected
allocation/VM/signal/pthread functions. It resets before each phase and snapshots
before printing. It forwards to real host functions; it is not a replacement
runtime. Calls made internally inside shared libc are not observed. Existing
alternate signal stacks/sanitizers may change counts in another environment.

Both -O0/-O2 observed the same counts on each of two initialization cycles:

| Phase | Observed nonzero direct calls |
|---|---|
| Initial exit before init | None |
| Init | calloc 2; malloc 1; sysconf 2; sigaction 2; sigaltstack 2; pthread_getattr_np 1; pthread_attr_getstack 1; pthread_attr_destroy 1 |
| Repeated init while ready | None |
| Successful ge_add(19, 23) | None; returns 42 |
| Exit | free 5; sigaction 2; sigaltstack 1; pthread_mutex_lock 1; pthread_mutex_unlock 1 |
| Repeated exit while cold | None |

The free count includes thread bookkeeping/free(NULL); it is not a count of
non-null live allocations. No observed phase called mmap, mprotect or munmap.
Zero data regions avoid actual data mapping, but do not avoid initialization.
This does not establish that all host-process allocations are counted or that
future target code is allocation-free.

Separate processes verify calling an export before init or after exit exits 1
with the initialization guard message; adding INT32_MAX + 1 with GS_DEBUG=1 exits
1 with an overflow diagnostic. All three negative cases pass at both levels.
These are current desktop behavior that the proposed profile must preserve at
its platform panic boundary.

## Static undefined symbols versus runtime calls

Native -O2 leaf object with GS_DEBUG=1 needs:
`calloc`, `free`, `gs_panic`, `gs_ovf`, `gs_rt_start_d22ae129d92b`, `gs_rt_stop`.
Without debug checks, the earlier exploratory object omitted gs_ovf; debug checks
are mandatory in the proposed profile. At -O0 many unused static helpers also
leave references to scanning/math/memory/cast/division functions. See the raw
inventories rather than treating the -O2 list as universal.

The emitted runtime object includes filesystem/dynamic loader and thread APIs,
including services no leaf call reaches. --gc-sections reduces the linked set,
but native-stack inspection, signal handling, allocator calls and shutdown
locking remain. The observer itself also contributes libc references; the
linked executable's undefined-symbol list is not purely Goose dependencies.
Source tracing, per-object symbols and phase observations therefore answer
three different questions. No MCU footprint can be inferred from host object
or executable size.

## Counterexamples: zero regions are not a profile

At Goose -O0 each of tests/profile_candidates/{foreign,recursive,reference}.goose
compiles successfully and reports zero main/global data regions:

- foreign: scalar extern could invoke arbitrary unverified C services.
- recursive: declared recursive scalar function can consume unbounded native
  call depth (the compiler also has a recursion marker requirement).
- reference: scalar reference parameter crosses a pointer-bearing ABI.

Also, `-DGS_MAX_STACKS=0` accepts examples/growth.goose with two data regions.
[CheckStackLimit](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/src/codegen_stacks.h#L105)
enforces the maximum only when maxstacks > 0. These files are tests of upstream
acceptance and evidence for a stronger validator; **no profile rejection was
tested**, because the profile does not exist yet.

## Investigation corrections

The first draft probe looked only on stderr for --stacks reports; this compiler
writes these reports to stdout during C emission. Fixed the probe to inspect
both captured streams. A first recursion fixture omitted Goose's required
`recursive fn` declaration and was rejected by normal typechecking; corrected
it using the pinned upstream recursion examples. Neither failure was a target
runtime issue; final logs contain the corrected reproducible probes.

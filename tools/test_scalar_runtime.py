#!/usr/bin/env python3
"""Host scalar-runtime lifecycle/dependency/ABI probes. Never accesses hardware."""
import argparse
import json
import os
from pathlib import Path
import random
import subprocess

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler', type=Path, required=True)
p.add_argument('--source', type=Path, default=ROOT / '.cache/goose-scalar-runtime')
p.add_argument('--cc', default='cc')
p.add_argument('--clang', default='clang')
a = p.parse_args()
a.compiler, a.source = a.compiler.resolve(), a.source.resolve()
out = ROOT / 'build/scalar-runtime-tests'
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, GOOSE_STDLIB=str(a.source / 'stdlib'), GOOSE_HOME=str(out / 'home'))
records, summary = [], {}
wrap = ['calloc', 'malloc', 'free', 'sysconf', 'sigaction', 'sigaltstack',
        'mmap', 'mprotect', 'munmap', 'pthread_getattr_np', 'pthread_attr_getstack',
        'pthread_attr_destroy', 'pthread_mutex_lock', 'pthread_mutex_unlock']

def require(ok, message):
    if not ok: raise SystemExit(f'FAIL: {message}; see {out / "results.json"}')

def run(argv, code=0):
    argv = list(map(str, argv))
    r = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    records.append(dict(command=argv, returncode=r.returncode, expected_returncode=code,
                        stdout=r.stdout, stderr=r.stderr))
    (out / 'results.json').write_text(json.dumps(records, indent=2)+'\n')
    require(r.returncode == code, f'{argv}: got {r.returncode}, expected {code}')
    return r

run([a.compiler, 'version'])
run([a.cc, '--version'])
run([a.clang, '--version'])
for level in (0, 2):
    work = out / f'O{level}'
    work.mkdir(exist_ok=True)
    cflags = ['-std=c11', f'-O{level}']  # No LTO, section GC, -lm or -pthread.
    emitted = []
    for name in ('accepted', 'arithmetic'):
        c, h, obj = work / f'{name}.c', work / f'{name}.h', work / f'{name}.o'
        run([a.compiler, '--embedded-profile=scalar-v0', f'-O{level}', '--stacks',
             '--header', h, '-o', c, ROOT / f'tests/scalar_v0/{name}.goose'])
        run([a.cc, *cflags, '-c', c, '-o', obj])
        symbols = run(['nm', '-u', obj]).stdout
        names = {line.split()[-1] for line in symbols.splitlines() if line.strip()}
        require(names == {'ge_scalar_v0_panic_v1'}, f'unexpected profile object symbols: {names}')
        # Generic 32-bit freestanding compile: C portability evidence, not Xtensa.
        run([a.clang, '--target=i386-unknown-none-elf', '-ffreestanding', '-nostdlibinc',
             *cflags, '-c', c, '-o', work / f'{name}-i386.o'])
        symbols32 = run(['nm', '-u', work / f'{name}-i386.o']).stdout
        names32 = {line.split()[-1] for line in symbols32.splitlines() if line.strip()}
        require(names32 <= {'ge_scalar_v0_panic_v1', '__muldi3'}, f'freestanding symbols: {names32}')
        emitted.append(dict(name=name, undefined=sorted(names), i386_undefined=sorted(names32)))

    common = ['-I', work, '-I', ROOT / 'tests']
    profile = work / 'accepted.o'
    clean = work / 'clean-host'
    run([a.cc, *cflags, *common, profile, ROOT / 'tests/scalar_v0/lifecycle_host.c',
         ROOT / 'tests/scalar_v0/panic_host.c', '-o', clean])
    run([clean])
    final_symbols = run(['nm', '-u', clean]).stdout
    require(not any(line.split()[-1].split('@')[0] in wrap for line in final_symbols.splitlines()
                    if line.strip()), 'clean executable retains a forbidden direct dependency')
    observed = work / 'observed-host'
    run([a.cc, *cflags, *common, '-DGE_OBSERVE', profile,
         ROOT / 'tests/scalar_v0/lifecycle_host.c', ROOT / 'tests/scalar_v0/panic_host.c',
         ROOT / 'tests/runtime_observer.c', *[f'-Wl,--wrap={x}' for x in wrap], '-o', observed])
    phases = [json.loads(line) for line in run([observed]).stdout.splitlines()]
    require([p['phase'] for p in phases] == ['exit-before-init'] +
            ['init', 'repeat-init', 'export', 'exit', 'repeat-exit'] * 2, 'lifecycle transitions')
    require(all(not any(p['calls'].values()) for p in phases), 'observed forbidden runtime call')
    modes = {
        'before-init': 'goose_init must be called before exported functions',
        'after-exit': 'goose_init must be called before exported functions',
        'bad-argc': 'invalid initialization arguments',
        'bad-argv': 'invalid initialization arguments',
        'bad-ready-args': 'invalid initialization arguments',
        'overflow': 'i32 overflow', 'add-overflow': 'i32 overflow',
        'mul-overflow': 'i32 overflow', 'neg-overflow': 'i32 overflow',
    }
    for mode, message in modes.items():
        r = run([observed, mode], 1)
        require(message in r.stderr, f'panic category {mode}')
        if 'overflow' in mode:
            require('accepted.goose' in r.stderr, 'arithmetic panic source location')

    # Missing/wrong hook version must fail to link; no default panic stub exists.
    missing = run([a.cc, *cflags, *common, profile,
                   ROOT / 'tests/scalar_v0/lifecycle_host.c', '-o', work / 'missing-hook'], 1)
    require('ge_scalar_v0_panic_v1' in missing.stderr, 'missing hook link error')
    wrong = work / 'wrong-hook.c'
    wrong.write_text('#include <stdlib.h>\nvoid ge_scalar_v0_panic_v2(const char *m, const char *f, int l) { _Exit(1); }\n')
    r = run([a.cc, *cflags, *common, profile, ROOT / 'tests/scalar_v0/lifecycle_host.c',
             wrong, '-o', work / 'wrong-hook'], 1)
    require('ge_scalar_v0_panic_v1' in r.stderr, 'wrong hook link version')
    run([a.cc, *cflags, '-DGE_SCALAR_V0_ABI_VERSION=2', '-c', work / 'accepted.c',
         '-o', work / 'wrong-abi.o'], 1)
    bad = work / 'unchecked.c'
    bad.write_text((work / 'accepted.c').read_text().replace('#define GS_DEBUG 1', '#define GS_DEBUG 0', 1))
    run([a.cc, *cflags, '-c', bad, '-o', work / 'unchecked.o'], 1)
    bad.write_text((work / 'accepted.c').read_text().replace('0 == 0 && 0 == 0 && 0 == 0',
                                                          '1 == 0 && 0 == 0 && 0 == 0', 1))
    run([a.cc, *cflags, '-c', bad, '-o', work / 'nonzero-regions.o'], 1)

    calc = work / 'arithmetic-host'
    run([a.cc, *cflags, *common, '-DGE_OBSERVE', '-DGE_PROFILE_HEADER="arithmetic.h"',
         work / 'arithmetic.o', ROOT / 'tests/scalar_v0/arithmetic_host.c',
         ROOT / 'tests/scalar_v0/panic_host.c', ROOT / 'tests/runtime_observer.c',
         *[f'-Wl,--wrap={x}' for x in wrap], '-o', calc])
    rng = random.Random(0)
    edges = [-2147483648, -2147483647, -1, 0, 1, 46340, 46341, 2147483647]
    pairs = [(x, y) for x in edges for y in edges]
    pairs += [(rng.randint(-2**31, 2**31-1), rng.randint(-2**31, 2**31-1)) for _ in range(16)]
    for op in ('add', 'sub', 'mul', 'neg'):
        for x, y in (pairs if op != 'neg' else [(x, 0) for x in edges]):
            expected = {'add': x+y, 'sub': x-y, 'mul': x*y, 'neg': -x}[op]
            valid = -2**31 <= expected <= 2**31-1
            r = run([calc, op, x, y], 0 if valid else 1)
            require(r.stdout == f'{expected}\n' if valid else 'i32 overflow' in r.stderr,
                    f'checked arithmetic mismatch {op} {x} {y}')
    summary[f'O{level}'] = dict(objects=emitted, phases=phases,
                               clean_host_undefined=final_symbols.splitlines(),
                               arithmetic_cases=3*len(pairs)+len(edges))

reserved = out / 'reserved.goose'
reserved.write_text('export "ge_scalar_v0_panic_v1" fn bad(a: i32) -> i32 { return a; }\n')
r = run([a.compiler, '--embedded-profile=scalar-v0', '--header', out / 'reserved.h',
         '-o', out / 'reserved.c', reserved], 1)
require('reserved for the panic ABI' in r.stderr, 'panic symbol namespace reservation')
(out / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
print(f'PASS: {len(records)} runtime commands; source/object evidence in {out}')

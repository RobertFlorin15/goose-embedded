#!/usr/bin/env python3
"""Linux/GNU host inspection of pinned separate-runtime startup; no target code."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler', type=Path, required=True)
p.add_argument('--source', type=Path, default=ROOT / '.cache/goose')
p.add_argument('--cc', default='cc')
p.add_argument('--nm', default='nm')
a = p.parse_args()
a.compiler = a.compiler.resolve()
a.source = a.source.resolve()
out = ROOT / 'build/runtime-probe'
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, GOOSE_STDLIB=str(a.source / 'stdlib'),
           GOOSE_HOME=str(out / 'goose-home'))
records = []
summary = {}

def run(args, code=0):
    args = [str(x) for x in args]
    r = subprocess.run(args, cwd=ROOT, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    records.append(dict(command=args, returncode=r.returncode,
                        stdout=r.stdout, stderr=r.stderr, expected_returncode=code))
    (out / 'results.json').write_text(json.dumps(records, indent=2) + '\n')
    if r.returncode != code:
        raise SystemExit(f'FAIL: {args}: expected {code}, got {r.returncode}; see {out}')
    return r

pin = json.loads((ROOT / 'research/upstream.json').read_text())['goose']['commit']
assert run(['git', '-C', a.source, 'rev-parse', 'HEAD']).stdout.strip() == pin
assert not run(['git', '-C', a.source, 'status', '--porcelain']).stdout.strip()
run([a.compiler, 'version'])
run([a.cc, '--version'])
run([a.nm, '--version'])
run([a.compiler, '--emit-runtime', out / 'runtime.c'])
wrapped = ['calloc', 'malloc', 'free', 'sysconf', 'sigaction', 'sigaltstack',
           'mmap', 'mprotect', 'munmap', 'pthread_getattr_np', 'pthread_attr_getstack',
           'pthread_attr_destroy', 'pthread_mutex_lock', 'pthread_mutex_unlock']

for level in (0, 2):
    # Goose optimization, native C optimization and debug checks are explicit.
    # GS_DEBUG=1 is embedded in program C; separate runtime handles both modes.
    result = run([a.compiler, f'-O{level}', '-DGS_DEBUG=1', '--stacks', '--header',
                  out / 'leaf.h', '-o', out / 'leaf.c', ROOT / 'examples/leaf.goose'])
    assert '0 data stacks + 0 global stacks = 0 regions' in (result.stdout + result.stderr)
    flags = ['-std=c11', f'-O{level}', '-ffunction-sections', '-fdata-sections']
    for name in ('leaf', 'runtime'):
        run([a.cc, *flags, '-c', out / f'{name}.c', '-o', out / f'{name}-O{level}.o'])
    program_symbols = run([a.nm, '-u', out / f'leaf-O{level}.o']).stdout
    runtime_symbols = run([a.nm, '-u', out / f'runtime-O{level}.o']).stdout
    exe = out / f'lifecycle-O{level}'
    run([a.cc, *flags, '-I', out, '-I', ROOT / 'tests',
         out / f'leaf-O{level}.o', out / f'runtime-O{level}.o',
         ROOT / 'tests/runtime_lifecycle_host.c', ROOT / 'tests/runtime_observer.c',
         '-Wl,--gc-sections', *[f'-Wl,--wrap={s}' for s in wrapped],
         '-o', exe, '-lm', '-pthread'])
    linked_symbols = run([a.nm, '-u', exe]).stdout
    phases = [json.loads(line) for line in run([exe]).stdout.splitlines()]
    assert len(phases) == 11
    assert [x['phase'] for x in phases] == ['exit-before-init'] + [
        'init', 'repeat-init', 'export', 'exit', 'repeat-exit'] * 2
    for phase in phases:
        counts = phase['calls']
        if phase['phase'] == 'init':
            assert counts['calloc'] >= 2 and counts['sigaction'] > 0
        elif phase['phase'] == 'exit':
            assert counts['free'] >= 2 and counts['sigaction'] > 0
        else:
            assert not any(counts.values())
        assert counts['mmap'] == counts['mprotect'] == counts['munmap'] == 0
    for mode in ('before-init', 'after-exit'):
        failure = run([exe, mode], code=1)
        assert 'goose_init must be called before exported functions' in failure.stderr
    failure = run([exe, 'overflow'], code=1)
    assert 'overflow' in failure.stderr
    summary[f'O{level}'] = dict(program_undefined=program_symbols.splitlines(),
                               runtime_undefined=runtime_symbols.splitlines(),
                               linked_undefined=linked_symbols.splitlines(), phases=phases)

# These are counterexamples to zero-region-only enforcement, not profile tests.
for name in ('foreign', 'recursive', 'reference'):
    r = run([a.compiler, '-O0', '--stacks', '--header', out / f'{name}.h',
             '-o', out / f'{name}.c', ROOT / f'tests/profile_candidates/{name}.goose'])
    assert '0 data stacks + 0 global stacks = 0 regions' in (r.stdout + r.stderr)
    summary[name] = 'upstream accepts with zero regions; proposed profile must reject'
r = run([a.compiler, '-DGS_MAX_STACKS=0', '--stacks', '-o', out / 'growth.c',
         ROOT / 'examples/growth.goose'])
assert '2 data stacks + 0 global stacks = 2 regions' in (r.stdout + r.stderr)
summary['max_stacks_zero'] = 'upstream accepts two regions: zero disables limit'
(out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(f'PASS: {len(records)} host commands; startup traces and symbols in {out}')

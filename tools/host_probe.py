#!/usr/bin/env python3
"""Pinned host-only compiler/C ABI probes. No downloads or hardware access."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, default=ROOT / '.cache/goose')
p.add_argument('--compiler', type=Path, required=True)
p.add_argument('--cc', default='cc', help='single C compiler executable')
a = p.parse_args()
a.source = a.source.resolve()
a.compiler = a.compiler.resolve()
out = ROOT / 'build/host-probe'
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, GOOSE_STDLIB=str(a.source / 'stdlib'),
           GOOSE_HOME=str(out / 'goose-home'))
records = []

def run(args, expected=None):
    args = [str(x) for x in args]
    r = subprocess.run(args, cwd=ROOT, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    record = dict(command=args, returncode=r.returncode, stdout=r.stdout, stderr=r.stderr)
    records.append(record)
    (out / 'results.json').write_text(json.dumps(records, indent=2) + '\n')
    if r.returncode or (expected is not None and r.stdout != expected):
        raise SystemExit(f'FAIL: {args}; see {out / "results.json"}')
    return r.stdout.strip()

pin = json.loads((ROOT / 'research/upstream.json').read_text())['goose']['commit']
if run(['git', '-C', a.source, 'rev-parse', 'HEAD']) != pin:
    raise SystemExit('Source revision mismatch')
if run(['git', '-C', a.source, 'status', '--porcelain']):
    raise SystemExit('Source has modifications; use clean pinned checkout')
run([a.compiler, 'version'])
run([a.cc, '--version'])
for name, expected in [('scalar', 'goose-embedded: 42\n'), ('growth', 'growth: 32\n')]:
    source = ROOT / f'examples/{name}.goose'
    run([a.compiler, 'check', source])
    run([a.compiler, '--standalone', '--stacks', '-o', out / f'{name}.c', source])
    run([a.cc, '-std=c11', '-O2', out / f'{name}.c', '-o', out / name, '-lm', '-pthread'])
    run([out / name], expected)
run([a.compiler, '--standalone', '--header', out / 'scalar.h',
     '-o', out / 'library.c', ROOT / 'examples/scalar.goose'])
run([a.cc, '-std=c11', '-O2', '-I', out, out / 'library.c', ROOT / 'tests/c_host.c',
     '-o', out / 'c_host', '-lm', '-pthread'])
run([out / 'c_host'], 'goose-embedded: 42\ngoose-embedded: 42\nc-host: 42; restarted twice\n')
run([a.compiler, '--standalone', '--stacks', '--header', out / 'leaf.h',
     '-o', out / 'leaf.c', ROOT / 'examples/leaf.goose'])
run([a.cc, '-std=c11', '-O2', '-I', out, '-DGE_HEADER="leaf.h"',
     out / 'leaf.c', ROOT / 'tests/c_host.c', '-o', out / 'leaf_host', '-lm', '-pthread'])
run([out / 'leaf_host'], 'c-host: 42; restarted twice\n')
run([a.cc, '-m32', '-std=c11', '-ffreestanding', '-c', ROOT / 'tests/layout_witness.c',
     '-o', out / 'layout32.o'])
print(f'PASS: {len(records)} host commands; results in {out / "results.json"}')

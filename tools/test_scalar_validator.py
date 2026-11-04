#!/usr/bin/env python3
"""Validate the patched scalar-v0 frontend; checks both frontend stages and host behavior."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import hashlib

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler', type=Path, required=True)
p.add_argument('--source', type=Path)
p.add_argument('--validator-only', action='store_true')
p.add_argument('--cc', default='cc')
a = p.parse_args()
a.compiler = a.compiler.resolve()
a.source = (a.source or ROOT / ('.cache/goose-scalar' if a.validator_only else '.cache/goose-scalar-runtime')).resolve()
out = ROOT / 'build/scalar-validator-tests'
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, GOOSE_STDLIB=str(a.source / 'stdlib'), GOOSE_HOME=str(out / 'home'))
records = []

def require(condition, message):
    if not condition:
        raise SystemExit(f'FAIL: {message}; see {out / "results.json"}')

def run(argv, code=0):
    argv = list(map(str, argv))
    r = subprocess.run(argv, cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
    records.append(dict(command=argv, returncode=r.returncode, expected_returncode=code,
                        stdout=r.stdout, stderr=r.stderr))
    (out / 'results.json').write_text(json.dumps(records, indent=2)+'\n')
    require(r.returncode == code, f'{argv}: got {r.returncode}, expected {code}')
    return r

cases = json.loads((ROOT / 'tests/scalar_v0/rejections.json').read_text())
for name, source in cases.items():
    (out / f'{name}.goose').write_text(source+'\n')
# A build sidecar must be rejected before its contents are interpreted.
(out / 'sidecar.goose').write_text((ROOT / 'examples/leaf.goose').read_text())
(out / 'sidecar.build').write_text('this is deliberately not a build file;')
# Import acceptance must never reach package fetching. GOOSE_HOME starts isolated.

for level in (0, 2):
    work = out / f'O{level}'
    work.mkdir(exist_ok=True)
    c, h = work / 'accepted.c', work / 'accepted.h'
    flags = ['--embedded-profile=scalar-v0', f'-O{level}']
    run([a.compiler, *flags, '--stacks', '--header', h, '-o', c,
         ROOT / 'tests/scalar_v0/accepted.goose'])
    runtime_sources = [ROOT / 'tests/scalar_v0/panic_host.c']
    if a.validator_only:
        run([a.compiler, '--emit-runtime', work / 'runtime.c'])
        runtime_sources = [work / 'runtime.c']
    exe = work / 'host'
    run([a.cc, '-std=c11', f'-O{level}', '-I', work, c, *runtime_sources,
         ROOT / 'tests/scalar_v0/host.c', '-o', exe, '-lm', '-pthread'])
    r = run([exe])
    require('host semantics pass' in r.stdout, 'accepted scalar semantics')
    for mode in ('overflow', 'mul-overflow', 'add-overflow', 'neg-overflow'):
        r = run([exe, mode], 1)
        require('overflow' in r.stderr, f'profile must check {mode}')
    # Rejected source must preserve existing outputs, including a previous success.
    good = (c.read_bytes(), h.read_bytes())
    for name in [*cases, 'sidecar']:
        r = run([a.compiler, *flags, '--header', h, '-o', c, out / f'{name}.goose'], 1)
        require('scalar-v0:' in r.stderr, f'{name} must fail in profile validation')
        require((c.read_bytes(), h.read_bytes()) == good, f'{name} corrupted prior artifacts')
    require(not list(work.glob('*.tmp')), 'staging files leaked')
    # Unknown options/modes/defines must not execute early-return actions.
    conflicts = [
        ['--standalone'], ['--jit'], ['--parse'], ['--check'], ['--dump'],
        ['--unsafe-no-rf-check'], ['--no-bce'], ['--multi-test'], ['--roundtrip'],
        ['-DGS_DEBUG=0'], ['-D', 'GS_DEBUG=0'], ['-DGS_MAX_STACKS=0'],
        ['--include', 'not-read.h'], ['--stack-reserve', '64K'], ['--update'],
        ['--emit-runtime', work / 'forbidden-runtime.c'], ['--gen-runtime-header'],
        ['--help'], ['--compile-shader', 'not-read.vert'],
    ]
    for extra in conflicts:
        # Test early-return flags on both sides of the profile option.
        for args in ([*extra, *flags], [*flags, *extra]):
            r = run([a.compiler, *args, '--header', h, '-o', c, ROOT / 'examples/leaf.goose'], 1)
            require('scalar-v0:' in r.stderr, f'conflict {extra}')
            require((c.read_bytes(), h.read_bytes()) == good, f'conflict {extra} changed outputs')
    require(not (work / 'forbidden-runtime.c').exists(), 'early runtime emission bypass')
    for verb in ('run', 'build', 'check', 'fetch', 'format', 'version', 'toolchain', 'lsp'):
        r = run([a.compiler, verb, *flags, ROOT / 'examples/leaf.goose'], 1)
        require('scalar-v0:' in r.stderr, f'verb {verb} bypass')
    for bad in ('--embedded-profile=future', '--embedded-profile'):
        r = run([a.compiler, bad, '-o', c, '--header', h, ROOT / 'examples/leaf.goose'], 1)
        require('unknown embedded profile' in r.stderr, 'unknown profile')
    # Structured source diagnostics must retain profile/location information.
    r = run([a.compiler, *flags, '--diagnostics', 'json', '--header', h,
             '-o', c, out / 'array_dead.goose'], 1)
    diagnostics = json.loads(r.stdout)
    require(bool(diagnostics) and 'scalar-v0:' in json.dumps(diagnostics) and
            diagnostics[0]['line'] == 2 and diagnostics[0]['file'].endswith('array_dead.goose'),
            'JSON diagnostic source location')
    # Actual admitted source must keep desktop-only constructs valid without opt-in.
    for name in ('array', 'foreign', 'recursive', 'reference', 'builtin_dead', 'namespace', 'inferred_i64'):
        run([a.compiler, f'-O{level}', '--header', work / 'desktop.h', '-o',
             work / 'desktop.c', out / f'{name}.goose'])

# Missing outputs and aliased paths must not overwrite source or prior artifacts.
source = out / 'aliased.goose'
source.write_text((ROOT / 'examples/leaf.goose').read_text())
original = source.read_bytes()
link = out / 'source-link.goose'
if not link.exists(): link.symlink_to(source)
for c, h in ((source, out / 'alias.h'), (out / 'alias.c', link),
             (out / 'same', out / 'same')):
    r = run([a.compiler, '--embedded-profile=scalar-v0', '--header', h, '-o', c, source], 1)
    require('scalar-v0:' in r.stderr, 'aliased output diagnostic')
    require(source.read_bytes() == original, 'source changed through alias')
for flags in ([], ['-o', out / 'missing.c'], ['--header', out / 'missing.h']):
    run([a.compiler, '--embedded-profile=scalar-v0', *flags, source], 1)
# Staging failure must leave prior outputs intact and remove temporary files.
work = out / 'O0'
c, h = work / 'accepted.c', work / 'accepted.h'
good = c.read_bytes(), h.read_bytes()
blocked = out / 'blocked'
blocked.write_text('not a directory')
run([a.compiler, '--embedded-profile=scalar-v0', '--header', blocked / 'accepted.h',
     '-o', c, ROOT / 'examples/leaf.goose'], 1)
require((c.read_bytes(), h.read_bytes()) == good, 'staging failure changed prior outputs')
require(not list(work.glob('*.tmp')), 'staging failure leaked temporary file')
# A fresh archive + patch must reproduce the files used for this build exactly.
with tempfile.TemporaryDirectory(prefix='prepare-', dir=out) as temp:
    prepared = Path(temp) / 'source'
    run([sys.executable, ROOT / 'tools/prepare_scalar_compiler.py', '--destination', prepared,
         *(['--validator-only'] if a.validator_only else [])])
    metadata = json.loads((prepared / 'scalar-v0-provenance.json').read_text())
    require(metadata['patch_sha256'] == hashlib.sha256(
        (ROOT / 'patches/goose/0001-scalar-v0-validator.patch').read_bytes()).hexdigest(),
        'prepared patch fingerprint')
    selected = 'manifest.json' if a.validator_only else 'runtime-manifest.json'
    names = json.loads((ROOT / 'patches/goose' / selected).read_text())['files']
    for name in names:
        require((prepared / name).read_bytes() == (a.source / name).read_bytes(),
                f'patch did not reproduce {name}')
    run([sys.executable, ROOT / 'tools/prepare_scalar_compiler.py', '--destination', prepared], 1)
bad_pin = out / 'bad-pin-source'
run([sys.executable, ROOT / 'tools/prepare_scalar_compiler.py', '--upstream', ROOT,
     '--destination', bad_pin], 1)
require(not bad_pin.exists(), 'preparation wrote files before checking the pin')
# Profile-looking program arguments must not opt a normal desktop run in.
for word in ('--embedded-profile=scalar-v0', '--embedded-profile=future'):
    r = run([a.compiler, 'run', ROOT / 'examples/scalar.goose', '--', word])
    require(r.stdout == 'goose-embedded: 42\n', 'program argument mistaken for profile')
    run([a.compiler, 'check', '--stdlib', word, ROOT / 'examples/leaf.goose'])
# Existing host probe exercises unmodified CLI/build/runtime modes on the patched compiler.
run([sys.executable, ROOT / 'tools/host_probe.py', '--compiler', a.compiler,
     '--source', ROOT / '.cache/goose'])
print(f'PASS: {len(records)} validator/regression commands; see {out / "results.json"}')

#!/usr/bin/env python3
"""Prepare a disposable pinned Goose source tree with the tracked scalar compiler/runtime patches.

No downloads, original checkout mutation, or compiler build occurs.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--upstream', type=Path, default=ROOT / '.cache/goose')
p.add_argument('--destination', type=Path)
p.add_argument('--validator-only', action='store_true', help='prepare only the historical validator patch')
a = p.parse_args()
source = a.upstream.resolve()
dest = (a.destination or ROOT / ('.cache/goose-scalar' if a.validator_only else '.cache/goose-scalar-runtime')).resolve()
pin = json.loads((ROOT / 'research/upstream.json').read_text())['goose']['commit']
patch = ROOT / 'patches/goose/0001-scalar-v0-validator.patch'
manifest = json.loads((patch.parent / 'manifest.json').read_text())
runtime_patch = patch.parent / '0002-scalar-v0-runtime.patch'
runtime_manifest = {} if a.validator_only else json.loads((patch.parent / 'runtime-manifest.json').read_text())
if not a.validator_only and (runtime_manifest['upstream_commit'] != pin or
        runtime_manifest['validator_patch_sha256'] != manifest['patch_sha256'] or
        runtime_manifest['patch_sha256'] != hashlib.sha256(runtime_patch.read_bytes()).hexdigest()):
    raise SystemExit('Runtime patch/manifest pin or digest mismatch')
if manifest['upstream_commit'] != pin or manifest['patch_sha256'] != hashlib.sha256(patch.read_bytes()).hexdigest():
    raise SystemExit('Patch/manifest pin or digest mismatch')

def git(*args, **kwargs):
    return subprocess.run(['git', '-C', str(source), *args], check=True,
                          capture_output=True, **kwargs).stdout

if git('rev-parse', 'HEAD', text=True).strip() != pin:
    raise SystemExit('Refusing a source revision other than the project pin')
if git('status', '--porcelain', text=True).strip():
    raise SystemExit('Refusing a modified upstream checkout')
if dest.exists():
    raise SystemExit(f'Refusing existing destination: {dest}; choose a new disposable path')
archive = git('archive', '--format=tar', pin)
dest.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    tar.extractall(dest, filter='data')
# Do not let git apply discover this project's enclosing Git repository.
env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(dest.parent))
for selected_patch, selected_manifest in [(patch, manifest)] + ([] if a.validator_only else [(runtime_patch, runtime_manifest)]):
    for args in (['--check', '--whitespace=error'], []):
        subprocess.run(['git', 'apply', *args, str(selected_patch)], cwd=dest, env=env, check=True)
    for name, expected in selected_manifest['files'].items():
        if hashlib.sha256((dest / name).read_bytes()).hexdigest() != expected:
            raise SystemExit(f'Patched file differs from reviewed manifest: {name}')
metadata = dict(upstream_commit=pin, patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),
                scope='scalar-v0 validator only' if a.validator_only else 'scalar-v0 runtime ABI 1')
if not a.validator_only:
    metadata['runtime_patch_sha256'] = runtime_manifest['patch_sha256']
(dest / 'scalar-v0-provenance.json').write_text(json.dumps(metadata, indent=2)+'\n')
print(f'Prepared {dest}; configure/build separately per tools/README.md')

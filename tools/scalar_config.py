"""Snapshot ordered ESP-IDF defaults and publish local offline run manifests."""
import hashlib
from pathlib import Path
import re


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def defaults_inputs(base, overlays, configuration):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', configuration):
        raise ValueError('configuration ID must be 1..64 lowercase ASCII letters/digits/_/-')
    # SDK target-specific lookup follows the supplied pathname, including when
    # the base file is a symlink. Snapshot bytes, not links.
    paths = [Path(x).absolute() for x in [base, *overlays]]
    if len({x.resolve() for x in paths}) != len(paths):
        raise ValueError('duplicate defaults input')
    inputs = []
    for index, path in enumerate(paths):
        for suffix in ('', '.esp32s3'):
            p = Path(str(path) + suffix)
            if suffix and not p.exists():
                continue
            if not p.is_file():
                raise ValueError(f'defaults input is not a file: {p}')
            if any(x in str(p) for x in (';', '\n', '\r')):
                raise ValueError('CMake defaults paths must not contain list/newline delimiters')
            inputs.append({'original': str(p), 'snapshot': f'config-inputs/{index:02d}.defaults{suffix}',
                           'sha256': sha256(p)})
    return inputs


def snapshot_defaults(out, inputs):
    out = Path(out)
    (out / 'config-inputs').mkdir()
    for item in inputs:
        content = Path(item['original']).read_bytes()
        if hashlib.sha256(content).hexdigest() != item['sha256']:
            raise ValueError('defaults changed before snapshot')
        (out / item['snapshot']).write_bytes(content)
    return [str(out / x['snapshot']) for x in inputs if not x['snapshot'].endswith('.esp32s3')]


def verify_defaults(out, inputs):
    for item in inputs:
        if sha256(item['original']) != item['sha256'] or sha256(Path(out) / item['snapshot']) != item['sha256']:
            raise ValueError('defaults input or snapshot changed during build')


def validate_effective_config(config):
    lines = config.splitlines()
    for value in ('CONFIG_IDF_TARGET="esp32s3"', 'CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y'):
        if value not in lines:
            raise ValueError(f'missing required configuration: {value}')
    for key in ('CONFIG_ESP_DEBUG_OCDAWARE', 'CONFIG_ESP_TRACE_ENABLE',
                'CONFIG_ESP_SYSTEM_GDBSTUB_RUNTIME', 'CONFIG_ESP_COREDUMP_ENABLE', 'CONFIG_COMPILER_LTO'):
        if f'{key}=y' in lines:
            raise ValueError(f'incompatible configuration: {key}')


def run_manifest(work, level, configuration, inputs, compiler_hash, sdk_commit, case="success"):
    work = Path(work)
    config = (work / 'sdkconfig').read_text()
    match = re.search(r'^CONFIG_ESP_MAIN_TASK_STACK_SIZE=([0-9]+)$', config, re.M)
    if not match or 'CONFIG_IDF_TARGET="esp32s3"' not in config:
        raise ValueError('expected ESP32-S3 task-stack configuration')
    files = ['sdkconfig', 'firmware/goose_scalar.elf', 'firmware/goose_scalar.bin',
             'firmware/bootloader/bootloader.bin', 'firmware/partition_table/partition-table.bin']
    hashes = {name: sha256(work / name) for name in files}
    return {'schema_version': 1, 'kind': 'scalar-v0-build', 'configuration': configuration,
            'case': case, 'optimization': level, 'sdk_commit': sdk_commit, 'compiler_sha256': compiler_hash,
            'defaults': inputs, 'artifacts': hashes, 'main_stack_bytes': int(match.group(1)),
            'elf_sha256': hashes['firmware/goose_scalar.elf'],
            'evidence': 'cross-build/host tests only; no physical verification'}

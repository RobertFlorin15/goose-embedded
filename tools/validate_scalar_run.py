#!/usr/bin/env python3
"""Check a saved scalar telemetry log against local build artifacts. No hardware access.

This checks consistency of supplied files, never authenticates physical execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from scalar_config import validate_effective_config

HEX = re.compile(r'[0-9a-f]{64}')
FILES = {'sdkconfig', 'firmware/goose_scalar.elf', 'firmware/goose_scalar.bin',
         'firmware/bootloader/bootloader.bin', 'firmware/partition_table/partition-table.bin'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_json(path):
    return parse_json(Path(path).read_bytes())


def parse_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'duplicate JSON key: {key}')
            result[key] = value
        return result
    value = json.loads(data.decode('utf-8'), object_pairs_hook=unique)
    require(isinstance(value, dict), 'expected JSON object')
    return value


def local_file(root, name):
    require(isinstance(name, str) and not Path(name).is_absolute(), 'expected relative file path')
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), 'file escapes record directory or is absent')
    return path


def validate(manifest_path, capture_path):
    manifest_path, capture_path = Path(manifest_path), Path(capture_path)
    manifest_bytes = manifest_path.read_bytes()
    m, c = parse_json(manifest_bytes), read_json(capture_path)
    for item, kind in [(m, 'scalar-v0-build'), (c, 'scalar-v0-capture')]:
        require(type(item.get('schema_version')) is int and item['schema_version'] == 1,
                'unsupported schema version')
        require(item.get('kind') == kind, 'unexpected record kind')
    require(c.get('evidence_type') in ('synthetic', 'physical', 'simulator', 'unknown'),
            'explicit evidence_type required')
    require(c.get('manifest_sha256') == hashlib.sha256(manifest_bytes).hexdigest(), 'manifest hash mismatch')
    require(isinstance(m.get('configuration'), str) and
            re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', m['configuration']), 'invalid configuration ID')
    require(c.get('configuration') == m['configuration'], 'configuration mismatch')
    require(type(m.get('optimization')) is int and m['optimization'] in (0, 2), 'invalid build optimization')
    require(type(c.get('optimization')) is int and c['optimization'] == m['optimization'],
            'optimization mismatch')
    require(isinstance(m.get('sdk_commit'), str) and re.fullmatch(r'[0-9a-f]{40}', m['sdk_commit']),
            'invalid SDK revision identity')
    require(isinstance(m.get('compiler_sha256'), str) and HEX.fullmatch(m['compiler_sha256']),
            'invalid compiler identity')
    hashes = m.get('artifacts')
    require(isinstance(hashes, dict) and set(hashes) == FILES, 'incomplete artifact manifest')
    config = None
    for name, expected in hashes.items():
        require(isinstance(expected, str) and HEX.fullmatch(expected), 'invalid artifact digest')
        data = local_file(manifest_path.parent, name).read_bytes()
        require(hashlib.sha256(data).hexdigest() == expected, f'artifact hash mismatch: {name}')
        if name == 'sdkconfig':
            config = data.decode('utf-8')
    require(m.get('elf_sha256') == hashes['firmware/goose_scalar.elf'], 'inconsistent ELF identity')
    validate_effective_config(config)
    stack = re.search(r'^CONFIG_ESP_MAIN_TASK_STACK_SIZE=([0-9]+)$', config, re.M)
    require(stack is not None and type(m.get('main_stack_bytes')) is int and
            m['main_stack_bytes'] == int(stack[1]) > 0, 'task stack configuration mismatch')
    log_path = local_file(capture_path.parent, c.get('log'))
    with log_path.open('rb') as stream:
        log_bytes = stream.read(16 * 1024 * 1024 + 1)
    require(len(log_bytes) <= 16 * 1024 * 1024, 'log exceeds 16 MiB inspection limit')
    require(c.get('log_sha256') == hashlib.sha256(log_bytes).hexdigest(), 'log hash mismatch')
    lines = log_bytes.decode('utf-8').splitlines()
    fatal = re.compile(r"Guru Meditation|panic'ed|abort\(\) was called|Backtrace:|stack canary|CPU halted|Brownout|"
                       r"Stack smashing|stack overflow|assert failed:|Task watchdog got triggered", re.I)
    require(not any(fatal.search(x) for x in lines), 'fatal diagnostic in normal-path capture')
    protocol = [(i, line.strip()) for i, line in enumerate(lines) if 'goose-embedded' in line]
    require(len(protocol) == 4, 'expected one complete four-line telemetry sequence')
    first, identity = protocol[0]
    require(identity == f"goose-embedded identity-v1: elf_sha256={m['elf_sha256']}", 'firmware identity mismatch')
    require(protocol[1][1] == 'goose-embedded scalar-v0: 42', 'missing or wrong scalar result/order')
    match = re.fullmatch(r'goose-embedded stack-v1: before=(0|[1-9][0-9]{0,9}) '
                         r'after_goose=(0|[1-9][0-9]{0,9}) '
                         r'after_result_print=(0|[1-9][0-9]{0,9}) bytes', protocol[2][1])
    require(match is not None, 'missing or malformed stack report/order')
    require(protocol[3][1] == 'goose-embedded completed-v1', 'missing application completion marker')
    # A normal boot prefix is allowed; no reset/second boot after app identity.
    reset = re.compile(r'^\s*(ESP-ROM:|rst:|boot:)', re.I)
    require(not any(reset.search(x) for x in lines[first + 1:]), 'reset/boot after application identity')
    require(sum('ESP-ROM:' in x for x in lines) <= 1, 'multiple boot sessions')
    values = list(map(int, match.groups()))
    require(all(0 <= x <= m['main_stack_bytes'] for x in values), 'stack reading outside configured range')
    require(values == sorted(values, reverse=True), 'increasing low-water readings require review')
    debugger = c.get('debugger')
    if debugger is not None:
        keys = ('before', 'after_goose', 'after_result_print', 'after_report', 'completed')
        require(isinstance(debugger, dict) and set(debugger) == set(keys) and
                all(type(debugger.get(k)) is int for k in keys), 'invalid debugger sample types/fields')
        require(debugger['completed'] == 4, 'partial debugger record')
        require([debugger[k] for k in keys[:3]] == values, 'debugger/log readings mismatch')
        require(0 <= debugger['after_report'] <= values[-1], 'invalid post-report reading')
    return {'status': 'consistent', 'scope': 'supplied-file consistency only; not authenticated execution',
            'declared_evidence_type': c['evidence_type'], 'hardware_execution_proven': False,
            'stack_bound_proven': False, 'configuration': m['configuration'], 'optimization': m['optimization'],
            'elf_sha256': m['elf_sha256'], 'log_sha256': c['log_sha256'],
            'serial_samples_bytes': dict(zip(('before', 'after_goose', 'after_result_print'), values)),
            'debugger_samples': debugger, 'zero_reading_present': 0 in values or
            (debugger is not None and debugger['after_report'] == 0)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--capture', type=Path, required=True)
    a = p.parse_args()
    try:
        result = validate(a.manifest, a.capture)
    except (ValueError, OSError) as error:
        print(json.dumps({'status': 'rejected', 'error': str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())

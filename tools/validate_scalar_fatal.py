#!/usr/bin/env python3
"""Check saved fatal-case diagnostics against artifacts; no hardware access or attestation."""
import argparse
import json
from pathlib import Path
import re
import sys

from validate_scalar_run import load_capture, require

MESSAGES = {'cold-export': 'goose_init must be called before exported functions',
            'overflow': 'i32 overflow'}


def validate(manifest_path, capture_path):
    m, c, lines = load_capture(manifest_path, capture_path)
    case = m.get('case')
    require(case in MESSAGES, 'fatal validator requires an explicit fatal build case')
    require(c.get('case') == case, 'explicit fatal capture case required')
    require(c.get('debugger') is None, 'normal stack debugger record not applicable to fatal case')
    protocol = [(i, x.strip()) for i, x in enumerate(lines) if 'goose-embedded' in x]
    require(len(protocol) == 2, 'expected only identity and fatal-case protocol lines')
    first, identity = protocol[0]
    require(identity == f"goose-embedded identity-v1: elf_sha256={m['elf_sha256']}", 'firmware identity mismatch')
    require(protocol[1][1] == f'goose-embedded case-v1: {case}', 'wrong fatal case/order')
    # The pinned SDK prints abort details verbatim, then eventually this halt cue.
    # Do not require addresses, backtrace shape or the shortened SDK ELF digest.
    details = [i for i, x in enumerate(lines) if x.strip() == MESSAGES[case]]
    halts = [i for i, x in enumerate(lines) if x.strip() == 'CPU halted.']
    require(len(details) == len(halts) == 1, 'missing or duplicate expected details/halt cue')
    require(protocol[1][0] < details[0] < halts[0], 'fatal diagnostic order mismatch')
    require(not any(x.strip() for x in lines[halts[0] + 1:]), 'content after terminal halt cue')
    reset = re.compile(r'^\s*(ESP-ROM:|rst:|boot:)', re.I)
    require(not any(reset.search(x) for x in lines[first + 1:]), 'reset after application identity')
    require(sum('ESP-ROM:' in x for x in lines) <= 1, 'multiple boot sessions')
    unrelated = re.compile(r"Guru Meditation|panic'ed|abort\(\) was called|Brownout|stack canary|"
                           r"Stack smashing|stack overflow|assert failed:|watchdog|Rebooting|"
                           r"fatal case unexpectedly returned|invalid initialization arguments|unreachable scalar code", re.I)
    for i, line in enumerate(lines):
        require(not unrelated.search(line), 'unexpected fault/reset diagnostic')
        if 'Backtrace:' in line:
            require(details[0] < i < halts[0], 'backtrace outside expected fatal interval')
        if i != details[0]:
            require(not any(message in line for message in MESSAGES.values()), 'conflicting/repeated fatal details')
    return {'status': 'consistent', 'case': case, 'expected_message': MESSAGES[case],
            'scope': 'supplied-file consistency only; not authenticated execution or proof of halt',
            'declared_evidence_type': c['evidence_type'], 'hardware_execution_proven': False,
            'halt_proven': False, 'stack_bound_proven': False, 'configuration': m['configuration'],
            'optimization': m['optimization'], 'elf_sha256': m['elf_sha256'], 'log_sha256': c['log_sha256']}


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

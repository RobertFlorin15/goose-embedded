#!/usr/bin/env python3
"""Retain pinned fatal-path disassembly and individual frames; never a stack bound.

Read-only with respect to SDK/builds. No hardware or target execution. Requires
existing passing cold-export/overflow scalar probe outputs and local SDK tools.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from esp_idf_baseline import ROOT, PIN, digest, verify_sdk
from scalar_config import validate_effective_config
from validate_scalar_run import parse_json, local_file, require, FILES

SYMBOLS = (
    'vPortTaskWrapper', 'main_task', 'app_main', 'ge_add',
    'ge_scalar_v0_panic_v1', 'esp_system_abort', 'panic_abort',
    '_xt_user_exc', '_xt_handle_exc', '_xt_context_save',
    '_WindowOverflow4', '_WindowOverflow8', '_WindowOverflow12',
    'xt_unhandled_exception', 'panic_enable_cache', 'panic_handler',
    'esp_panic_handler', 'print_abort_details', 'print_state', 'print_state_for_core',
    'panic_print_backtrace', 'esp_backtrace_print_from_frame', 'esp_backtrace_get_next_frame',
    'panic_print_str', 'panic_print_char', 'panic_print_char_uart', 'panic_print_char_usb_serial_jtag',
    'uart_hal_write_txfifo', 'esp_panic_handler_increment_entry_count',
    'esp_panic_handler_enable_rtc_wdt', 'esp_panic_handler_disable_timg_wdts',
    'esp_panic_handler_reset_modules_on_exit_and_halt', 'esp_system_reset_modules_on_exit',
)
HELPERS = ('gs_panic', 'add_g', 'gs_add_i32', 'gs_scalar_overflow')
SOURCES = (
    'components/esp_system/panic.c', 'components/esp_system/port/panic_handler.c',
    'components/esp_system/port/esp_system_chip.c',
    'components/esp_system/port/arch/xtensa/panic_arch.c',
    'components/esp_system/port/arch/xtensa/debug_helpers.c',
    'components/xtensa/xtensa_vectors.S', 'components/xtensa/xtensa_context.S',
    'components/xtensa/include/xt_asm_utils.h', 'components/xtensa/xtensa_intr_asm.S',
    'components/xtensa/xtensa_intr.c',
    'components/esp_system/port/soc/esp32s3/system_internal.c',
)


def inspect(text, symbol):
    """Extract one labelled symbol only; absent entry is unknown, never zero."""
    match = re.search(r'^([0-9a-f]+) <' + re.escape(symbol) + r'>:\n(.*?)(?=\n[0-9a-f]+ <|\Z)',
                      text, re.M | re.S)
    require(match is not None, f'missing disassembly symbol: {symbol}')
    body = match[2]
    frames = re.findall(r'\bentry\s+a1,\s*([0-9]+)', body)
    require(len(frames) <= 1, f'multiple entry instructions: {symbol}')
    return {'address': match[1], 'entry_frame_bytes': int(frames[0]) if frames else None,
            'direct_calls': re.findall(r'\bcall(?:0|4|8|12)\s+[0-9a-f]+ <([^>]+)>', body),
            'indirect_call_count': len(re.findall(r'\bcallx(?:0|4|8|12)\b', body)),
            'assembly_sha256': hashlib.sha256(body.encode()).hexdigest()}


def audit(builds, sdk, objdump, out):
    require(not out.exists(), 'fresh audit output required')
    # Keep output away from input trees; inspection never changes evidence.
    for source in (sdk, objdump.parent, *builds, ROOT / 'examples', ROOT / 'src'):
        require(not (out == source or out.is_relative_to(source) or source.is_relative_to(out)),
                'output overlaps input tree')
    pin = parse_json(PIN.read_bytes())
    verify_sdk(sdk, pin)
    require('esp-15.2.0_20251204' in str(objdump), 'expected pinned local disassembler')
    result = {'status': 'incomplete', 'scope': 'static source/artifact inspection only',
              'hardware_execution_proven': False, 'stack_bound_proven': False,
              'sdk_commit': pin['commit'], 'objdump_sha256': digest(objdump),
              'sdk_sources': {p: digest(sdk / p) for p in SOURCES}, 'builds': []}
    out.mkdir(parents=True)
    try:
        for index, build in enumerate(builds):
            original = parse_json((build / 'results.json').read_bytes())
            require(original.get('status') == 'pass', 'passing scalar probe required')
            require(original.get('sdk_pin') == pin, 'probe SDK pin mismatch')
            for name, expected in original.get('source_hashes', {}).items():
                require(digest(local_file(ROOT, name)) == expected, f'build source mismatch: {name}')
            case = original.get('case')
            require(case in ('cold-export', 'overflow'), 'fatal build case required')
            for level in (0, 2):
                work = build / f'O{level}'
                manifest = work / 'run-manifest.json'
                m = parse_json(manifest.read_bytes())
                require(type(m.get('schema_version')) is int and m['schema_version'] == 1 and
                        m.get('kind') == 'scalar-v0-build', 'unsupported build manifest')
                require(m.get('case') == case and type(m.get('optimization')) is int and
                        m['optimization'] == level and m.get('sdk_commit') == pin['commit'],
                        'case/optimization/revision mismatch')
                require(isinstance(m.get('artifacts'), dict) and set(m['artifacts']) == FILES,
                        'incomplete build artifacts')
                for name, expected in m['artifacts'].items():
                    require(digest(local_file(work, name)) == expected, f'artifact mismatch: {name}')
                require(m.get('elf_sha256') == m['artifacts']['firmware/goose_scalar.elf'],
                        'inconsistent ELF identity')
                require(m['elf_sha256'] == original['levels'][f'O{level}']['artifacts']['goose_scalar.elf']['sha256'],
                        'ELF differs from passing probe')
                config = (work / 'sdkconfig').read_text()
                validate_effective_config(config)
                for setting in ('CONFIG_ESP_CONSOLE_UART=y',
                                'CONFIG_ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG=y'):
                    require(setting in config.splitlines(), 'audit currently reviews UART + secondary USB console only')
                elf = work / 'firmware/goose_scalar.elf'
                prefix = f'{index}-{case}-O{level}'
                argv = [str(objdump), '-d', str(elf)]
                proc = subprocess.run(argv, capture_output=True, text=True, check=True)
                log = out / f'{prefix}-assembly.log'
                log.write_text(proc.stdout)
                records = {name: inspect(proc.stdout, name) for name in SYMBOLS}
                if level == 0:
                    records.update({name: inspect(proc.stdout, name) for name in HELPERS})
                path = ['vPortTaskWrapper', 'main_task', 'app_main', 'ge_add']
                if level == 0:
                    path += ['gs_panic'] if case == 'cold-export' else ['add_g', 'gs_add_i32', 'gs_scalar_overflow']
                path += ['ge_scalar_v0_panic_v1', 'esp_system_abort', 'panic_abort']
                frames = [records[name]['entry_frame_bytes'] for name in path]
                require(all(type(x) is int for x in frames), 'expected entry frame on reviewed pre-trap path')
                # This is a manually source/assembly-reviewed path, not automatic
                # reachability, inclusive cost, window-spill or worst-case analysis.
                result['builds'].append({'case': case, 'optimization': level,
                    'probe': str(build), 'probe_sha256': digest(build / 'results.json'),
                    'manifest_sha256': digest(manifest), 'elf_sha256': digest(elf),
                    'sdkconfig_sha256': digest(work / 'sdkconfig'), 'command': argv,
                    'assembly_log': log.name, 'assembly_log_sha256': digest(log), 'symbols': records,
                    'reviewed_pre_trap_path': path, 'visible_entry_frame_sum_bytes': sum(frames),
                    'sum_is_stack_bound': False,
                    'console_config': [x for x in config.splitlines() if x.startswith('CONFIG_ESP_CONSOLE')],
                    'isr_stack_config': next(x for x in config.splitlines() if x.startswith('CONFIG_FREERTOS_ISR_STACKSIZE='))})
        verify_sdk(sdk, pin)
        result['status'] = 'pass'
    except Exception as error:
        result.update(status='failed', error=str(error))
        raise
    finally:
        (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, action='append', required=True)
    p.add_argument('--sdk', type=Path, default=ROOT / '.cache/esp-idf-v6.0.2')
    p.add_argument('--objdump', type=Path, default=ROOT / '.cache/espressif/tools/xtensa-esp-elf/esp-15.2.0_20251204/xtensa-esp-elf/bin/xtensa-esp32s3-elf-objdump')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        result = audit([x.resolve() for x in a.build], a.sdk.resolve(), a.objdump.resolve(), a.output.resolve())
    except (ValueError, OSError, subprocess.CalledProcessError, RuntimeError) as error:
        sys.exit(str(error))
    print(f"PASS: {len(result['builds'])} fatal ELF inspections; no stack bound or hardware evidence")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Build/inspect scalar-v0 on ESP32-S3 and test its C panic bridge on Linux.

No flash, monitor, serial access or target execution. Requires prepared SDK/compiler.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from esp_idf_baseline import ROOT, PIN, capture, digest, verify_sdk


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiler', type=Path, default=ROOT / 'build/goose-scalar-runtime/goose')
    p.add_argument('--sdk', type=Path, default=ROOT / '.cache/esp-idf-v6.0.2')
    p.add_argument('--tools', type=Path, default=ROOT / '.cache/espressif')
    p.add_argument('--output', type=Path, default=ROOT / 'build/esp-idf-scalar')
    p.add_argument('--jobs', type=int, default=2)
    a = p.parse_args()
    compiler, sdk, tools, out = (x.resolve() for x in (a.compiler, a.sdk, a.tools, a.output))
    source = ROOT / '.cache/goose-scalar-runtime'
    if out.exists() or a.jobs < 1:
        p.error('use a fresh output and positive --jobs')
    if any(' ' in str(x) for x in (compiler, sdk, tools, out, ROOT)):
        p.error('ESP-IDF paths must not contain spaces')
    if any(out == x or out.is_relative_to(x) or x.is_relative_to(out)
           for x in (sdk, tools, source, compiler.parent, ROOT / 'examples', ROOT / 'src')):
        p.error('output must be separate from source/compiler/SDK/tools')
    pin = json.loads(PIN.read_text())
    submodules = verify_sdk(sdk, pin)
    baseline = json.loads((ROOT / 'research/esp-idf-baseline-results.json').read_text())
    if baseline['status'] != 'pass' or baseline['pin'] != pin:
        raise RuntimeError('A reviewed passing SDK baseline at this pin is required')
    manifest = json.loads((ROOT / 'patches/goose/runtime-manifest.json').read_text())
    for name, sha in manifest['files'].items():
        if digest(source / name) != sha:
            raise RuntimeError(f'Compiler source differs from runtime manifest: {name}')
    if '335fddc+scalar-v0-runtime' not in capture([str(compiler), 'version']):
        raise RuntimeError('Expected the scalar runtime compiler')
    out.mkdir(parents=True)
    result = {'status': 'incomplete', 'scope': 'target compilation/static inspection + host stub execution only',
              'sdk_pin': pin, 'submodules': submodules, 'compiler_sha256': digest(compiler),
              'compiler_version': capture([str(compiler), 'version']),
              'runtime_patch_sha256': manifest['patch_sha256'],
              'baseline_app_bytes': baseline['artifacts']['hello_world.bin']['bytes'],
              'commands': [], 'levels': {}}

    def save():
        (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')

    def run(argv, name, env, cwd=None, expected=0):
        argv = list(map(str, argv))
        log = out / f'{name}.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('w') as f:
            proc = subprocess.run(argv, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT)
        result['commands'].append({'argv': argv, 'cwd': str(cwd or ROOT), 'log': f'{name}.log',
                                   'exit_code': proc.returncode, 'expected': expected})
        save()
        if proc.returncode != expected:
            raise RuntimeError(f'{name}: exit {proc.returncode}, expected {expected}; see {log}')
        return log.read_text()

    save()
    try:
        env = dict(os.environ)
        for key in ('IDF_PATH', 'IDF_PYTHON_ENV_PATH', 'IDF_TARGET', 'VIRTUAL_ENV',
                    'SDKCONFIG', 'SDKCONFIG_DEFAULTS', 'EXTRA_COMPONENT_DIRS'):
            env.pop(key, None)
        env.update(IDF_TOOLS_PATH=str(tools), IDF_CCACHE_ENABLE='0', CCACHE_DISABLE='1',
                   PIP_CACHE_DIR=str(ROOT / '.cache/pip'), PYTHONNOUSERSITE='1')
        activation = subprocess.run(
            ['bash', '-c', 'source "$1/export.sh" >&2 && python -c '
             "'import json,os; print(json.dumps(dict(os.environ)))'", 'scalar', str(sdk)],
            env=env, text=True, capture_output=True)
        (out / 'activation.log').write_text(activation.stderr)
        if activation.returncode:
            raise RuntimeError('SDK activation failed; see activation.log')
        target_env = json.loads(activation.stdout)  # Never persist the complete environment.
        python = Path(target_env['IDF_PYTHON_ENV_PATH']) / 'bin/python'
        packages = run([python, '-m', 'pip', 'freeze', '--all'], 'python-packages', target_env)
        lock = ROOT / 'tools/esp-idf-python.lock'
        if packages.strip() != lock.read_text().strip():
            raise RuntimeError('Python environment differs from the package lock')
        result['python_lock_sha256'] = digest(lock)
        cc = shutil.which('xtensa-esp32s3-elf-gcc', path=target_env['PATH'])
        if not cc or not Path(cc).resolve().is_relative_to(tools):
            raise RuntimeError('Expected project-local target compiler')
        if capture([cc, '-dumpfullversion'], env=target_env) != pin['gcc_version']:
            raise RuntimeError('Unexpected target GCC version')
        prefix = str(Path(cc).parent / 'xtensa-esp32s3-elf-')
        result['gcc_version'] = capture([cc, '--version'], env=target_env)
        goose_env = dict(os.environ, GOOSE_STDLIB=str(source / 'stdlib'), GOOSE_HOME=str(out / 'goose-home'))
        inputs = [*Path(ROOT / 'examples/esp32s3_scalar').rglob('*'),
                  *Path(ROOT / 'src/platform/esp_idf').rglob('*'), ROOT / 'examples/leaf.goose']
        result['source_hashes'] = {str(x.relative_to(ROOT)): digest(x) for x in sorted(inputs) if x.is_file()}
        for level in (0, 2):
            name = f'O{level}'
            work = out / name
            work.mkdir()
            fw = work / 'firmware'
            idf = [python, sdk / 'tools/idf.py', '-C', ROOT / 'examples/esp32s3_scalar', '-B', fw,
                   '-D', f'SDKCONFIG={work / "sdkconfig"}', '-D', f'GOOSE_COMPILER={compiler}',
                   '-D', f'GE_SCALAR_OPT={level}', '-D', f'GE_PROJECT_ROOT={ROOT}']
            run([*idf, 'set-target', 'esp32s3'], f'{name}/configure', target_env)
            run(['cmake', '--build', fw, '--parallel', a.jobs], f'{name}/build', target_env)
            commands = json.loads((fw / 'compile_commands.json').read_text())
            entry = next(x for x in commands if x['file'].endswith('/ge_leaf.c'))
            c = Path(entry['file'])
            header = c.with_suffix('.h')
            argv = shlex.split(entry['command'])
            obj = Path(entry['directory']) / argv[argv.index('-o') + 1]
            undefined = run([prefix + 'nm', '-u', obj], f'{name}/leaf-undefined', target_env)
            symbols = sorted(line.split()[-1] for line in undefined.splitlines() if line.strip())
            if symbols != ['ge_scalar_v0_panic_v1']:
                raise RuntimeError(f'Unexpected leaf dependencies: {symbols}')
            run([prefix + 'objdump', '-dr', obj], f'{name}/leaf-assembly', target_env)
            bridge_entry = next(x for x in commands if x['file'].endswith('/scalar_panic.c'))
            bridge_argv = shlex.split(bridge_entry['command'])
            bridge_obj = Path(bridge_entry['directory']) / bridge_argv[bridge_argv.index('-o') + 1]
            bridge_nm = run([prefix + 'nm', '-u', bridge_obj], f'{name}/bridge-undefined', target_env)
            bridge_symbols = sorted(x.split()[-1] for x in bridge_nm.splitlines() if x.strip())
            if bridge_symbols != ['esp_system_abort']:
                raise RuntimeError(f'Unexpected bridge dependencies: {bridge_symbols}')
            run([prefix + 'objdump', '-dr', bridge_obj], f'{name}/bridge-assembly', target_env)
            for own in (entry, bridge_entry, next(x for x in commands if x['file'].endswith('/app_main.c'))):
                flags = shlex.split(own['command'])
                if [x for x in flags if x.startswith('-O')][-1] != f'-O{level}' or '-fno-lto' not in flags:
                    raise RuntimeError('Component optimization/LTO settings were not honored')
            elf = fw / 'goose_scalar.elf'
            elf_header = run([prefix + 'readelf', '-h', elf], f'{name}/elf-header', target_env)
            if not all(s in elf_header for s in ('ELF32', 'little endian', 'Tensilica Xtensa')):
                raise RuntimeError('Unexpected ELF architecture')
            final = run([prefix + 'nm', '--defined-only', elf], f'{name}/symbols', target_env)
            final_names = {x.split()[-1] for x in final.splitlines() if x.strip()}
            if not {'ge_add', 'goose_init', 'goose_exit', 'ge_scalar_v0_panic_v1',
                    'ge_scalar_v0_last_panic', 'app_main'} <= final_names:
                raise RuntimeError('Required leaf/bridge symbols missing')
            run([prefix + 'objdump', '-d', elf], f'{name}/firmware-assembly', target_env)
            for symbol in ('app_main', 'esp_system_abort', 'panic_abort'):
                run([prefix + 'objdump', '-d', f'--disassemble={symbol}', elf],
                    f'{name}/{symbol}-assembly', target_env)
            run([*idf, 'size'], f'{name}/size', target_env)
            config = (work / 'sdkconfig').read_text()
            for value in ('CONFIG_IDF_TARGET="esp32s3"', 'CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y'):
                if value not in config: raise RuntimeError(f'Missing configuration: {value}')
            for key in ('CONFIG_ESP_DEBUG_OCDAWARE', 'CONFIG_ESP_TRACE_ENABLE',
                        'CONFIG_ESP_SYSTEM_GDBSTUB_RUNTIME', 'CONFIG_ESP_COREDUMP_ENABLE',
                        'CONFIG_COMPILER_LTO'):
                if f'{key}=y' in config: raise RuntimeError(f'Unexpected configuration: {key}')
            # Host double exercises the actual binding and its borrowed-pointer record.
            hostflags = ['-std=c11', f'-O{level}', '-I', c.parent,
                         '-I', ROOT / 'src/platform/esp_idf', '-I', ROOT / 'tests/esp_idf/stubs']
            run(['cc', *hostflags, '-c', c, '-o', work / 'leaf-host.o'], f'{name}/host-leaf', goose_env)
            host = work / 'bridge-host'
            run(['cc', *hostflags, '-Wall', '-Wextra', '-Werror', work / 'leaf-host.o',
                 ROOT / 'src/platform/esp_idf/scalar_panic.c', ROOT / 'tests/esp_idf/panic_bridge_host.c',
                 '-o', host], f'{name}/host-link', goose_env)
            for mode in ('success', 'direct', 'cold', 'bad-init', 'overflow', 'after-exit'):
                text = run([host, mode], f'{name}/host-{mode}', goose_env, expected=0 if mode == 'success' else 1)
                if mode != 'success' and 'host panic boundary verified' not in text:
                    raise RuntimeError('Host did not reach the verified SDK double')
            bad = work / 'bad-abi'
            bad.mkdir()
            (bad / 'ge_leaf.h').write_text(header.read_text().replace('GE_SCALAR_V0_ABI_VERSION 1',
                                                                    'GE_SCALAR_V0_ABI_VERSION 2'))
            mismatch = run(['cc', '-std=c11', '-I', bad, '-I', ROOT / 'src/platform/esp_idf',
                            '-I', ROOT / 'tests/esp_idf/stubs', '-c',
                            ROOT / 'src/platform/esp_idf/scalar_panic.c', '-o', bad / 'panic.o'],
                           f'{name}/reject-bad-abi', goose_env, expected=1)
            if 'requires scalar runtime ABI 1' not in mismatch:
                raise RuntimeError('Expected the adapter ABI diagnostic')
            policy = run(['cc', *hostflags, '-DCONFIG_ESP_DEBUG_OCDAWARE=1', '-c',
                          ROOT / 'src/platform/esp_idf/scalar_panic.c', '-o', bad / 'policy.o'],
                         f'{name}/reject-panic-policy', goose_env, expected=1)
            if 'requires minimal halt panic policy' not in policy:
                raise RuntimeError('Expected the adapter panic-policy diagnostic')
            # Additional accepted operators compile independently, without SDK headers.
            arithmetic = work / 'arithmetic.c'
            run([compiler, '--embedded-profile=scalar-v0', f'-O{level}', '--header',
                 work / 'arithmetic.h', '-o', arithmetic, ROOT / 'tests/scalar_v0/arithmetic.goose'],
                f'{name}/emit-arithmetic', goose_env)
            run([cc, '-std=c11', f'-O{level}', '-fno-lto', '-fstack-usage', '-c', arithmetic,
                 '-o', work / 'arithmetic.o'], f'{name}/compile-arithmetic', target_env)
            arithmetic_nm = run([prefix + 'nm', '-u', work / 'arithmetic.o'], f'{name}/arithmetic-undefined', target_env)
            arithmetic_symbols = sorted(x.split()[-1] for x in arithmetic_nm.splitlines() if x.strip())
            if not set(arithmetic_symbols) <= {'ge_scalar_v0_panic_v1', '__muldi3'}:
                raise RuntimeError(f'Unexpected arithmetic dependencies: {arithmetic_symbols}')
            stack = {str(x.relative_to(out)): x.read_text() for x in fw.rglob('*.su')}
            stack[str((work / 'arithmetic.su').relative_to(out))] = (work / 'arithmetic.su').read_text()
            artifacts = ['goose_scalar.elf', 'goose_scalar.bin', 'goose_scalar.map',
                         'bootloader/bootloader.bin', 'partition_table/partition-table.bin']
            result['levels'][name] = {'leaf_undefined': symbols, 'bridge_undefined': bridge_symbols,
                                     'arithmetic_undefined': arithmetic_symbols,
                                     'generated_c_sha256': digest(c), 'generated_header_sha256': digest(header),
                                     'leaf_compile_command': entry, 'sdkconfig_sha256': digest(work / 'sdkconfig'),
                                     'stack_usage': stack,
                                     'artifacts': {x: {'bytes': (fw / x).stat().st_size, 'sha256': digest(fw / x)}
                                                   for x in artifacts}}
            save()
        verify_sdk(sdk, pin)
        if any(digest(ROOT / x) != sha for x, sha in result['source_hashes'].items()):
            raise RuntimeError('Experiment inputs changed during build')
        result['status'] = 'pass'
        save()
        print(f'PASS: scalar ESP32-S3 cross-build and host bridge tests; {out / "results.json"}')
    except Exception as error:
        result.update(status='failed', error=str(error))
        save()
        raise


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))

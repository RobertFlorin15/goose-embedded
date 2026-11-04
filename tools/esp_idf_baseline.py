#!/usr/bin/env python3
"""Build the pinned, unchanged ESP-IDF hello_world. Never opens hardware ports."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "tools/esp-idf-pin.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(argv, **kwargs):
    return subprocess.check_output(argv, text=True, **kwargs).strip()


def verify_sdk(sdk, pin):
    if capture(["git", "-C", str(sdk), "rev-parse", "HEAD"]) != pin["commit"]:
        raise RuntimeError("ESP-IDF is not at the pinned commit")
    if capture(["git", "-C", str(sdk), "status", "--porcelain", "--untracked-files=all"]):
        raise RuntimeError("ESP-IDF checkout or submodules are dirty")
    raw = subprocess.check_output(
        ["git", "-C", str(sdk), "submodule", "status", "--recursive"], text=True
    )
    if not raw or any(line[0] != " " for line in raw.splitlines()):
        raise RuntimeError("Initialize every pinned submodule before building")
    if digest(sdk / "tools/tools.json") != pin["tools_json_sha256"]:
        raise RuntimeError("ESP-IDF tools manifest differs from the pin")
    return raw.splitlines()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, default=ROOT / ".cache/esp-idf-v6.0.2")
    parser.add_argument("--tools", type=Path, default=ROOT / ".cache/espressif")
    parser.add_argument("--output", type=Path, default=ROOT / "build/esp-idf-baseline")
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    sdk, tools, out = (p.resolve() for p in (args.sdk, args.tools, args.output))
    pin = json.loads(PIN.read_text())
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    if out.exists():
        parser.error("--output must not exist; use a fresh path to preserve evidence")
    if any(" " in str(p) for p in (sdk, tools, out)):
        parser.error("ESP-IDF does not support spaces in these paths")
    # Do not copy/build into an upstream checkout or tool installation.
    if any(out == p or out.is_relative_to(p) or p.is_relative_to(out) for p in (sdk, tools)):
        parser.error("output must be separate from SDK and tools")
    submodules = verify_sdk(sdk, pin)
    out.mkdir(parents=True)
    result = {"status": "incomplete", "evidence": "target compilation only; no execution",
              "pin": pin, "submodules": submodules, "commands": []}

    def save():
        (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")

    def run(argv, env, name, cwd=None):
        with (out / f"{name}.log").open("w") as log:
            process = subprocess.run(argv, env=env, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
        result["commands"].append({"argv": [str(x) for x in argv], "log": f"{name}.log",
                                   "exit_code": process.returncode})
        save()
        if process.returncode:
            raise RuntimeError(f"{name} failed ({process.returncode}); see {out / (name + '.log')}")

    save()
    try:
        env = os.environ.copy()
        for key in ("IDF_PATH", "IDF_PYTHON_ENV_PATH", "IDF_TARGET", "VIRTUAL_ENV",
                    "SDKCONFIG", "SDKCONFIG_DEFAULTS", "EXTRA_COMPONENT_DIRS"):
            env.pop(key, None)
        env.update(IDF_TOOLS_PATH=str(tools), IDF_CCACHE_ENABLE="0", CCACHE_DISABLE="1",
                   PIP_CACHE_DIR=str(ROOT / ".cache/pip"), PYTHONNOUSERSITE="1",
                   GIT_CEILING_DIRECTORIES=str(out))
        # Source upstream's environment in a child shell. Never persist/dump the
        # complete environment, which may contain unrelated credentials.
        activation = subprocess.run(
            ["bash", "-c", 'source "$1/export.sh" >&2 && python -c '
             "'import json,os; print(json.dumps(dict(os.environ)))'", "baseline", str(sdk)],
            env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        (out / "activation.log").write_text(activation.stderr)
        if activation.returncode:
            raise RuntimeError(f"SDK activation failed; see {out / 'activation.log'}")
        env = json.loads(activation.stdout)
        python = str(Path(env["IDF_PYTHON_ENV_PATH"]) / "bin/python")
        cc = shutil.which("xtensa-esp32s3-elf-gcc", path=env["PATH"])
        if not cc or not Path(cc).resolve().is_relative_to(tools):
            raise RuntimeError("Expected the project-local ESP32-S3 compiler")
        version = capture([cc, "-dumpfullversion"], env=env)
        if version != pin["gcc_version"]:
            raise RuntimeError(f"Unexpected target GCC: {version}")
        result["versions"] = {
            "gcc": capture([cc, "--version"], env=env),
            "python": capture([python, "--version"], env=env),
            "cmake": capture(["cmake", "--version"], env=env),
            "ninja": capture(["ninja", "--version"], env=env),
        }
        run([python, "-m", "pip", "freeze", "--all"], env, "python-packages")
        lock = ROOT / "tools/esp-idf-python.lock"
        if (out / "python-packages.log").read_text().strip() != lock.read_text().strip():
            raise RuntimeError("Installed Python packages differ from tools/esp-idf-python.lock")
        result["python_packages_sha256"] = digest(lock)
        # Record the live constraints (upstream may refresh this file daily).
        result["python_constraints"] = {
            p.name: digest(p) for p in tools.glob("espidf.constraints.*.txt")
        }
        project = out / "hello_world"
        original = sdk / "examples/get-started/hello_world"
        shutil.copytree(original, project)
        hashes = {str(p.relative_to(original)): digest(p)
                  for p in sorted(original.rglob("*")) if p.is_file()}
        result["original_files"] = hashes
        idf = [python, str(sdk / "tools/idf.py"), "-B", str(out / "firmware")]
        run([*idf, "set-target", "esp32s3"], env, "set-target", project)
        # Use CMake's standard build interface for a bounded Ninja job count;
        # idf.py v6.0.2 does not expose a -j option.
        run(["cmake", "--build", str(out / "firmware"), "--parallel", str(args.jobs)],
            env, "build", project)
        # Verify byte identity of original files after both configuration/build.
        if any(digest(project / p) != sha for p, sha in hashes.items()):
            raise RuntimeError("Upstream example files changed during the experiment")
        if 'CONFIG_IDF_TARGET="esp32s3"' not in (project / "sdkconfig").read_text():
            raise RuntimeError("Unexpected configured target")
        fw = out / "firmware"
        description = json.loads((fw / "project_description.json").read_text())
        if description["target"] != "esp32s3":
            raise RuntimeError("Build description is not ESP32-S3")
        artifacts = ["hello_world.elf", "hello_world.bin", "hello_world.map",
                     "bootloader/bootloader.bin", "partition_table/partition-table.bin",
                     "project_description.json", "compile_commands.json", "flasher_args.json"]
        result["artifacts"] = {p: {"sha256": digest(fw / p), "bytes": (fw / p).stat().st_size}
                               for p in artifacts}
        result["sdkconfig_sha256"] = digest(project / "sdkconfig")
        prefix = str(Path(cc).parent / "xtensa-esp32s3-elf-")
        run([prefix + "readelf", "-h", str(fw / "hello_world.elf")], env, "elf-header")
        run([*idf, "size"], env, "size", project)
        elf_header = (out / "elf-header.log").read_text()
        if not all(value in elf_header for value in ("Tensilica Xtensa", "ELF32", "little endian")):
            raise RuntimeError("ELF is not 32-bit little-endian Xtensa")
        verify_sdk(sdk, pin)
        result["status"] = "pass"
        save()
        print(f"PASS: unchanged official ESP32-S3 baseline; evidence: {out / 'results.json'}")
    except Exception as error:
        result.update(status="failed", error=str(error))
        save()
        raise


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))

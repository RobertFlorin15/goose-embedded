# License and distribution inventory

Collected 2026-11-06 by static inspection of pinned inputs. **This is an
evidence inventory, not legal advice, a compatibility clearance, or a project
license selection.** Classification names the well-known license text a file
starts with; `unclassified` means "read it manually". Which files reach a given
binary is a separate, partly unresolved question (see Unresolved).

Reviewed tool output: [license-inventory-results.json](license-inventory-results.json)
(sha256 156071f34ccf34de85a57c0222f475baf8ad85f15e62444d623ea6cc9e96209d).

## Inputs and reproduction

| Input | Pin | Verification |
|---|---|---|
| Goose | [335fddc](https://github.com/aardappel/goose/tree/335fddc13dc74666398ffe160ec8a8f2958329d0) | clean checkout at pin |
| ESP-IDF | [v6.0.2 / 7101770](https://github.com/espressif/esp-idf/tree/7101770dc6db2667b3c477cc31365dd1acd6db4e), tag object b0d7ee87 | verify_sdk: clean, 25 recursive submodules initialized, tools.json sha256 matches; submodule commits equal those in esp32s3-scalar-results.json |
| Xtensa toolchain | esp-15.2.0_20251204 linux-amd64 archive | sha256 3d50f5cd...602b8 matches tools/esp-idf-pin.json; only `share/licenses/` members read |
| Python lock | tools/esp-idf-python.lock (58 packages) | hashed; package licenses **not inspected** |

```sh
git clone https://github.com/aardappel/goose.git .cache/goose
git -C .cache/goose checkout --detach 335fddc13dc74666398ffe160ec8a8f2958329d0
# ESP-IDF: either the full setup clone in tools/README.md, or this lighter one:
git clone --filter=blob:none --no-checkout https://github.com/espressif/esp-idf.git .cache/esp-idf-v6.0.2-meta
git -C .cache/esp-idf-v6.0.2-meta checkout --detach 7101770dc6db2667b3c477cc31365dd1acd6db4e
git -C .cache/esp-idf-v6.0.2-meta submodule update --init --recursive --depth 1 --filter=blob:none
mkdir -p .cache/dist && curl -L -o .cache/dist/xtensa-esp-elf-15.2.0_20251204-x86_64-linux-gnu.tar.xz \
  https://github.com/espressif/crosstool-NG/releases/download/esp-15.2.0_20251204/xtensa-esp-elf-15.2.0_20251204-x86_64-linux-gnu.tar.xz
python3 tools/license_inventory.py --sdk .cache/esp-idf-v6.0.2-meta \
  --toolchain-archive .cache/dist/xtensa-esp-elf-15.2.0_20251204-x86_64-linux-gnu.tar.xz \
  --output build/license-inventory-new
python3 -m unittest tests/test_license_inventory.py -v
```

The tool is offline and read-only. It refuses an existing output, a wrong or
dirty Goose/ESP-IDF checkout, uninitialized submodules, submodule drift from
recorded build evidence, and a toolchain archive whose hash differs from the pin.
Verified this session: 8 unit tests pass and the 47 existing scalar tests still pass. The tool also
refused, without writing output, a non-pinned archive and a Goose checkout with an
untracked file.

## Goose 335fddc (compiler host side)

| Component | License evidence | Reaches |
|---|---|---|
| Goose compiler/runtime | [LICENSE](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/LICENSE) Apache-2.0 text; **no root NOTICE file** | compiler binary; runtime text emitted into generated C |
| [third_party/tinycc](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/third_party/tinycc/README.md) (TinyCC 0fb5430, locally modified) | COPYING LGPL-2.1 text; RELICENSING is a **partial** MIT-style statement with explicit NO/? entries (e.g. arm-gen.c, tcccoff.c) | statically linked `libtcc` in every compiler ([libtcc.cmake](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/cmake/libtcc.cmake)); not optional |
| tinycc `lib/libtcc1.c` | header: GPL-2.0-or-later with an unlimited-linking exception | `libtcc1.a`, linked into programs the in-process JIT backend compiles |
| tinycc `win32/include/_mingw.h` etc. | "not copyrighted / public domain" headers (sampled) | Windows JIT headers |
| [third_party/subprocess](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/third_party/subprocess/README.md) | Unlicense (text at top of subprocess.h) | compiler (process runner) |
| [third_party/cute_spirv](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/third_party/cute_spirv/README.md) | cute_spirv.h: zlib OR Unlicense; ckit.h: "Public domain" | compiler (`goose_shaderc`, always built) |
| vscode/ | Apache-2.0 text | editor extension; not used here |

Upstream's [scripts/package_release.py](https://github.com/aardappel/goose/blob/335fddc13dc74666398ffe160ec8a8f2958329d0/scripts/package_release.py)
collects third_party license files into a `licenses/` directory of its release
archives: a useful model if this project ever ships compiler binaries.

REFERENCES.md previously named only TinyCC among Goose's third parties.
subprocess.h and cute_spirv/ckit are also compiled into every compiler.

## ESP-IDF v6.0.2 (firmware side)

Root LICENSE: Apache-2.0 text. In-tree SPDX census of `components/` (tracked
files excluding submodules; first 4 KiB scanned): 7578 Apache-2.0, 3180 with no
identifier (docs, Kconfig, CMake, binaries, etc.), 223 Unlicense OR CC0-1.0,
137 CC0-1.0, 98 MIT, 44 BSD-3-Clause, 9 BSD-2-Clause-FreeBSD AND Apache-2.0,
6 Apache-2.0 OR MIT, 2 BSD-2-Clause, 2 ISC, 1 BSD-4-Clause-UC.
Non-Apache code in components every ESP32-S3 image is likely to use:

- freertos: FreeRTOS-Kernel sources and Xtensa port MIT (71 files; SBOM 10.5.1, AWS originator).
- xtensa: Cadence-origin files MIT (12) plus 1 Apache-2.0 OR MIT.
- esp_libc: 9 BSD-2-Clause-FreeBSD AND Apache-2.0, 5 MIT (several are RISC-V/PSRAM-only).
- heap/tlsf submodule: **no root license file**; per-file SPDX BSD-3-Clause (Matthew Conte).
- esp_rom: BSD-3-Clause ROM USB headers (headers only).
- bootloader micro-ecc submodule: BSD-2-Clause-style LICENSE.txt; whether the
  current bootloader configuration links it is unresolved.

Submodules (all 25, root license files): Apache-2.0 text for Espressif binary
libraries (bt lib_esp32/c3, ble_mesh, coex, phy, wifi, thread lib) and NimBLE;
**Apache-2.0 OR GPL-2.0-or-later** for both mbedtls copies and the mbedtls framework;
BSD-style for lwIP, OpenThread, protobuf-c, micro-ecc; MIT-style for CMock,
Unity (x2), SPIFFS. Only `NOTICE` files exist for bt libs c2/c5/c6/h2 (NimBLE
attribution text, unclassified). CMock's vendored c_exception has no root
license file. None of BT, Wi-Fi, mbedtls, lwIP, OpenThread or SPIFFS are known
to be linked into the current scalar app, but no linker map confirms it.

C library: [esp_libc Kconfig](https://github.com/espressif/esp-idf/blob/7101770dc6db2667b3c477cc31365dd1acd6db4e/components/esp_libc/Kconfig)
defaults to **picolibc** with GCC (newlib only with Clang or explicit selection).
The project's sdkconfig.defaults do not override this, so prior GCC builds
presumably used picolibc. This follows from the Kconfig source; no saved effective sdkconfig
on this machine confirms it.

## Xtensa toolchain esp-15.2.0_20251204

tools.json declares `xtensa-esp-elf` as GPL-3.0-with-GCC-exception. The archive's
`share/licenses/` holds 105 files for automake, binutils, crosstool-ng, gcc, gmp,
isl, mpc, mpfr, newlib, picolibc, zlib, zstd. Relevant to firmware output:

- libgcc (linked into firmware): GCC tree ships GPL-3.0 text plus
  COPYING.RUNTIME (GCC Runtime Library Exception 3.1 text).
- picolibc 1.8.10: COPYING.picolibc is a Debian-format per-file manifest with 85
  license stanzas, overwhelmingly BSD-2/3-style and other permissive texts. Its
  copyleft stanzas name only `test/printf-tests.c`, `test/testcases.c` (GPL-2)
  and `scripts/GeneratePicolibcCrossFile.sh` (AGPL-3): test/build files, not
  library sources by name. Whether any archive member derives from them was not checked.
- newlib COPYING.NEWLIB: per-file notices with a default list (Red Hat BSD etc.);
  relevant only if newlib is selected.
- Twelve files are unclassified, all crosstool-ng CC BY-SA deed/legal-code assets,
  GCC m2 FDL, and zstd build LICENSE. None are firmware inputs.

Declared tools.json licenses for tools installed for esp32s3 (metadata only,
archives not inspected): GDB, esp32ulp-elf, ccache GPL-3.0-or-later; OpenOCD,
QEMU, dfu-util GPL-2.0-only; esp-clang, ninja, esp-rom-elfs, idf-exe Apache-2.0;
cmake BSD-3-Clause.

## Distribution scenarios

1. **This repository's source.** Original project code/docs/tests plus
   patches/goose (Apache-2.0 Goose diff context with LICENSE.upstream and
   modified-file notices). No upstream tree, SDK, toolchain or binary is tracked.
   The tests/esp_idf/stubs are 26 lines of declarations naming ESP-IDF APIs,
   written for host tests, not copied files. A project license is still needed
   before others can reuse original work; that choice is open.
2. **Compiler binaries (not currently distributed).** A patched Goose binary
   statically contains LGPL-2.1 TinyCC and ships beside GPL-2.0+-with-exception
   libtcc1.a, plus Unlicense/zlib/public-domain helpers. Distributing one would
   carry LGPL obligations for libtcc in addition to Apache-2.0 for Goose; this needs
   review before any binary release. Users building their own compiler locally
   from upstream do not create a distribution by this project.
3. **Generated C and firmware images.** Generated scalar C embeds the Goose-derived
   runtime (Apache-2.0, header states provenance). A distributed firmware image
   would also contain ESP-IDF Apache-2.0 code, MIT FreeRTOS/Xtensa files, BSD-3
   TLSF, picolibc permissive code and libgcc under the runtime exception, plus
   whatever else the linker map shows. Notices for these would need to accompany the
   image or its documentation. No firmware is distributed today.
4. **Local development only.** GPL tools (GDB, OpenOCD, QEMU, binutils, GCC
   itself) run on the developer's machine and are installed by ESP-IDF's
   installer. Downloads stay ignored under .cache/.

## Unresolved

- Exact linked object/component set per firmware: needs `build/*.map` and
  project_description.json from a fresh scalar build (prior build outputs are
  not on this machine). Until then, firmware notice lists are provisional.
- Effective libc (picolibc expected) from a saved effective sdkconfig.
- picolibc/libgcc archive membership versus their license manifests; GCC
  Runtime Library Exception eligibility is plausible for an unmodified GCC
  compile but is not asserted.
- Bootloader micro-ecc linkage under the reviewed configuration.
- Python lock package licenses (local tooling only; not distributed).
- Contents of NOTICE-only bt libraries and c_exception's README license section
  (not expected in the scalar firmware).
- Project license selection and any compatibility statement between it and
  Goose patch/runtime provenance.

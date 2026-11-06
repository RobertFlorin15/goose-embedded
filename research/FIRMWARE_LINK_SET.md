# Firmware link set and stated licenses

Collected 2026-11-06 from a fresh passing scalar cross-build. **Static evidence
for a future firmware notice list; not legal advice and not an execution result.**
No firmware is distributed, and nothing here was flashed or run.

Reviewed tool output: [firmware-link-set-results.json](firmware-link-set-results.json)
(sha256 719fd052cd9bbbb0cb18f85249178d3f72a7204c1df48cc241d8e56118ad2be9).

```sh
python3 tools/test_esp_idf_scalar.py --output build/esp-idf-scalar-license
python3 tools/firmware_link_set.py --build build/esp-idf-scalar-license --output build/firmware-link-set-new
python3 -m unittest tests/test_firmware_link_set.py -v
```

Build: default success case, control configuration, ESP-IDF 7101770, status pass,
83 commands. ELF sha256 O0 439d815f..., O2 cb9befda...; run manifests and the
effective sdkconfig hashes were checked against the files read.

## Method

An object counts only with nonzero bytes in an ELF section carrying SHF_ALLOC, read
from the ELF's own section table and summed from the linker map. This excludes
members that were pulled in and then garbage-collected, and debug-only content.
The tool refuses an image unless object bytes plus linker fill equal the allocated
total exactly, so nothing is silently unattributed. Each object is matched to its
source through compile_commands.json, and the license is what that source states
(SPDX, else a recognized text opening, else `none stated`). A repeat run produced
identical output.

## Results

| Image | Allocated | Object bytes | Fill/reserved | Objects |
|---|---|---|---|---|
| Application O0 | 376278 | 146093 | 230185 | 196 |
| Application O2 | 375958 | 145779 | 230179 | 196 |
| Bootloader O0/O2 | 21231 | 21022 | 209 | 31 |

Fill is mostly the linker's address-alignment reservations (`.ext_ram.dummy`,
`.flash_rodata_dummy`, `.dram0.dummy`), which is not code from any dependency.

Effective libc at both levels: `CONFIG_LIBC_PICOLIBC=y`.

Application at O2, by license stated in the linked source (O0 differs only in the
byte counts for Apache-2.0 and our own code):

| Stated license | Objects | Bytes | Sources |
|---|---|---|---|
| Apache-2.0 | 157 | 108756 | ESP-IDF components |
| MIT | 8 | 21286 | FreeRTOS-Kernel list/queue/tasks and Xtensa port; xtensa context, interrupt and vector assembly |
| BSD-3-Clause | 1 | 5238 | heap/tlsf/tlsf.c |
| Apache-2.0 OR GPL-2.0-or-later | 2 | 957 | mbedtls tf-psa-crypto psa_crypto.c, psa_crypto_slot_management.c |
| MIT-style text, no SPDX | 1 | 143 | xtensa/xtensa_intr.c |
| BSD-style text, no SPDX | 1 | 5 | esp_system/ubsan.c |
| Apache-2.0 text, no SPDX | 1 | 29 | esp_system debug_helpers_asm.S |
| none stated | 3 | 609 | our app_main.c and scalar_panic.c (root MIT); generated ge_leaf.c (Apache-2.0 runtime per its emitted header) |

Application objects with no source evidence:

| Origin | Bytes | Members | What is known |
|---|---|---|---|
| picolibc `libc.a` | 8103 | 15 (init, environ, tinystdio printf/bufio, Ryu float formatting) | Manifest matches by file name only: BSD-style for tinystdio/environ, Apache-2.0 for Ryu files, a permissive notice for misc/init.c. The GPL/AGPL stanzas name only test and script files. |
| `libxt_hal.a` (ESP-IDF prebuilt) | 437 | 4 | No source or license file for the archive itself. Its sibling Xtensa headers carry Cadence MIT text, which is suggestive only. |
| `libtfpsacrypto.a` | 216 | 3 (platform, platform_util, threading) | Source match failed because the objects build in a different directory; same mbedtls submodule, whose root states the dual license. |

The bootloader links 31 objects, all stating Apache-2.0.

## Answers to the inventory's open questions

- **libgcc:** no allocated bytes in any of the four images. Members are pulled
  into the link but contribute nothing to the image, so the GCC Runtime Library
  Exception question does not arise for this configuration. Do not generalize:
  another configuration or workload can link libgcc code.
- **Bootloader micro-ecc:** not linked with bytes. The component is absent from the
  bootloader's linked groups in this configuration (secure boot off).
- **mbedtls:** **the earlier inventory's "not known to be linked" was wrong.** About
  1.2 KB of PSA/mbedtls objects reach the application, though the example uses no
  cryptography itself. The dual license lets a distributor elect Apache-2.0.
- **Components:** project_description.json declares 50 components; 18 have no
  bytes in the application. A declared component is not evidence of linkage.

## Provisional notice list

For an image built from exactly this configuration, a notice file would need
Apache-2.0 (ESP-IDF, Goose-derived runtime, Ryu, PSA/mbedtls by election), MIT
(FreeRTOS, Xtensa, this project), BSD-3-Clause (TLSF, picolibc files per its
manifest) and picolibc's other permissive notices. Copyright lines must come from
the actual sources.

## Limits

- Code inlined from headers appears under the including object, not the header's
  own license. FreeRTOS, HAL and SoC headers can contribute this way.
- Espressif ROM code runs on the chip but is not in the image and is not counted.
- Results apply only to this configuration, case and SDK. Other board configs
  and future components need a separate run.
- Python package licenses and NOTICE-only Bluetooth libraries remain unreviewed;
  neither is in this image.
- This does not establish that the firmware runs. M2b remains unverified.

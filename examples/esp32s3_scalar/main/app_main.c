#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include "ge_leaf.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "stack_samples.h"
#include "esp_app_desc.h"

_Static_assert(GE_SCALAR_V0_ABI_VERSION == 1, "scalar runtime ABI 1 required");
_Static_assert(INCLUDE_uxTaskGetStackHighWaterMark == 1, "stack sampling API required");
_Static_assert(sizeof(StackType_t) == 1, "review stack watermark byte units on new ports");
_Static_assert(sizeof(UBaseType_t) <= sizeof(unsigned int) && UINT_MAX <= UINT32_MAX,
               "stack sample/console integer widths");

volatile struct ge_example_stack_samples ge_stack_samples;

#ifndef GE_SCALAR_CASE
#define GE_SCALAR_CASE 0
#endif
#if GE_SCALAR_CASE < 0 || GE_SCALAR_CASE > 2
#error "unknown scalar firmware case"
#endif

void app_main(void)
{
    /* ESP-IDF calls app_main in its normal main task. No workers or ISR entry. */
    ge_stack_samples.completed = 0;
    /* Full ELF digest from the SDK image descriptor, not its shortened log hash.
     * Fixed storage; single normal-task caller and caches available. */
    static char elf_hex[65];
    static const char digits[] = "0123456789abcdef";
    const esp_app_desc_t *description = esp_app_get_description();
    for (unsigned int i = 0; i < 32; ++i) {
        elf_hex[2 * i] = digits[description->app_elf_sha256[i] >> 4];
        elf_hex[2 * i + 1] = digits[description->app_elf_sha256[i] & 15];
    }
    elf_hex[64] = 0;
    esp_rom_printf("goose-embedded identity-v1: elf_sha256=%s\n", elf_hex);
    ge_stack_samples.before = uxTaskGetStackHighWaterMark(NULL);
    ge_stack_samples.completed = 1;
#if GE_SCALAR_CASE == 1
    esp_rom_printf("goose-embedded case-v1: cold-export\n");
    (void)ge_add(10, 32); /* Deliberately call before initialization. */
#elif GE_SCALAR_CASE == 2
    esp_rom_printf("goose-embedded case-v1: overflow\n");
    goose_init(0, NULL);
    (void)ge_add(INT32_MAX, 1); /* Deliberately exceed checked i32 range. */
#else
    goose_init(0, NULL);
    int32_t result = ge_add(10, 32);
    if (result != 42) {
        ge_scalar_v0_panic_v1("unexpected scalar result", __FILE__, __LINE__);
    }
    goose_exit();
    ge_stack_samples.after_goose = uxTaskGetStackHighWaterMark(NULL);
    ge_stack_samples.completed = 2;
    esp_rom_printf("goose-embedded scalar-v0: %d\n", (int)result);
    ge_stack_samples.after_result_print = uxTaskGetStackHighWaterMark(NULL);
    ge_stack_samples.completed = 3;
    esp_rom_printf("goose-embedded stack-v1: before=%u after_goose=%u after_result_print=%u bytes\n",
                   (unsigned int)ge_stack_samples.before,
                   (unsigned int)ge_stack_samples.after_goose,
                   (unsigned int)ge_stack_samples.after_result_print);
    /* This sample covers the report's own print call; keep it in the debugger
     * record rather than recursively printing measurements of measurements. */
    ge_stack_samples.after_report = uxTaskGetStackHighWaterMark(NULL);
    ge_stack_samples.completed = 4;
    esp_rom_printf("goose-embedded completed-v1\n");
    /* Returning lets ESP-IDF delete its main task. */
#endif
#if GE_SCALAR_CASE != 0
    /* A returning fatal call must never produce the expected diagnosis. */
    ge_scalar_v0_panic_v1("fatal case unexpectedly returned", __FILE__, __LINE__);
#endif
}

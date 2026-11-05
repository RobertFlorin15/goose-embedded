#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include "ge_leaf.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "stack_samples.h"

_Static_assert(GE_SCALAR_V0_ABI_VERSION == 1, "scalar runtime ABI 1 required");
_Static_assert(INCLUDE_uxTaskGetStackHighWaterMark == 1, "stack sampling API required");
_Static_assert(sizeof(StackType_t) == 1, "review stack watermark byte units on new ports");
_Static_assert(sizeof(UBaseType_t) <= sizeof(unsigned int) && UINT_MAX <= UINT32_MAX,
               "stack sample/console integer widths");

volatile struct ge_example_stack_samples ge_stack_samples;

void app_main(void)
{
    /* ESP-IDF calls app_main in its normal main task. No workers or ISR entry. */
    ge_stack_samples.completed = 0;
    ge_stack_samples.before = uxTaskGetStackHighWaterMark(NULL);
    ge_stack_samples.completed = 1;
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
    /* Returning lets ESP-IDF delete its main task. */
}

/* ESP-IDF binding for generated scalar-v0 ABI 1. No formatting or allocation. */
#include "ge_leaf.h"
#include "scalar_panic.h"
#include "esp_system.h"
#include "sdkconfig.h"

#if GE_SCALAR_V0_ABI_VERSION != 1
#error "ESP-IDF panic binding requires scalar runtime ABI 1"
#endif

#if !defined(CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT) || !CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT || \
    CONFIG_ESP_DEBUG_OCDAWARE || CONFIG_ESP_TRACE_ENABLE || \
    CONFIG_ESP_SYSTEM_GDBSTUB_RUNTIME || CONFIG_ESP_COREDUMP_ENABLE
#error "scalar adapter requires minimal halt panic policy"
#endif

volatile struct ge_scalar_v0_panic_record ge_scalar_v0_last_panic;

void ge_scalar_v0_panic_v1(const char *message, const char *file, int line)
{
    ge_scalar_v0_last_panic.message = message;
    ge_scalar_v0_last_panic.file = file;
    ge_scalar_v0_last_panic.line = line;
    /* Goose supplies static strings. SDK retains this pointer through panic.
     * Normal task/cache-enabled execution only; no ISR/cache-off contract. */
    esp_system_abort(message);
}

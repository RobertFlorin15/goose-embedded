#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include "ge_leaf.h"
#include "esp_rom_sys.h"

_Static_assert(GE_SCALAR_V0_ABI_VERSION == 1, "scalar runtime ABI 1 required");
_Static_assert(CHAR_BIT == 8 && sizeof(int32_t) == 4, "i32 target ABI");
_Static_assert(sizeof(void *) == 4 && sizeof(int) == 4, "ESP32-S3 C ABI");
_Static_assert(sizeof(gs_i32) == 4 && _Alignof(gs_i32) == 1, "Goose scalar alias");
_Static_assert(__builtin_types_compatible_p(__typeof__(&ge_add),
                                         int32_t (*)(int32_t, int32_t)), "export prototype");

void app_main(void)
{
    /* ESP-IDF calls app_main in its normal main task. No workers or ISR entry. */
    goose_init(0, NULL);
    int32_t result = ge_add(10, 32);
    if (result != 42) {
        ge_scalar_v0_panic_v1("unexpected scalar result", __FILE__, __LINE__);
    }
    goose_exit();
    esp_rom_printf("goose-embedded scalar-v0: %d\n", (int)result);
    /* Returning lets ESP-IDF delete its main task. */
}

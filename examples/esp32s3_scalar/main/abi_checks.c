/* Target-only witness; application logic can also be tested with host SDK doubles. */
#include <limits.h>
#include <stdint.h>
#include "ge_leaf.h"

_Static_assert(GE_SCALAR_V0_ABI_VERSION == 1, "scalar runtime ABI 1 required");
_Static_assert(CHAR_BIT == 8 && sizeof(int32_t) == 4, "i32 target ABI");
_Static_assert(sizeof(void *) == 4 && sizeof(int) == 4, "ESP32-S3 C ABI");
_Static_assert(sizeof(gs_i32) == 4 && _Alignof(gs_i32) == 1, "Goose scalar alias");
_Static_assert(__builtin_types_compatible_p(__typeof__(&ge_add),
                                         int32_t (*)(int32_t, int32_t)), "export prototype");

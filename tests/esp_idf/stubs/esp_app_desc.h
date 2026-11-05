#include <stdint.h>
/* Test double exposes only the descriptor member used by app_main. */
typedef struct { uint8_t app_elf_sha256[32]; } esp_app_desc_t;
const esp_app_desc_t *esp_app_get_description(void);

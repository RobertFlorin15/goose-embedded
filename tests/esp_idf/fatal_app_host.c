/* Real app/runtime/adapter; host SDK doubles. Never executes an ESP-IDF panic. */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "esp_app_desc.h"
#include "esp_system.h"
#include "esp_rom_sys.h"
#include "freertos/task.h"
#include "scalar_panic.h"
#include "stack_samples.h"

void app_main(void);
static const char *selected;
static unsigned phase;
static const esp_app_desc_t descriptor = {{0}};
const esp_app_desc_t *esp_app_get_description(void)
{
    if (phase || ge_stack_samples.completed) _Exit(90);
    return &descriptor;
}
UBaseType_t uxTaskGetStackHighWaterMark(TaskHandle_t task)
{
    if (task || phase != 1 || ge_stack_samples.completed) _Exit(91);
    phase = 2;
    return 3000;
}
int esp_rom_printf(const char *format, ...)
{
    char text[256];
    va_list args;
    va_start(args, format);
    int n = vsnprintf(text, sizeof(text), format, args);
    va_end(args);
    if (n < 0 || (size_t)n >= sizeof(text)) _Exit(92);
    if (phase == 0) {
        if (strcmp(text, "goose-embedded identity-v1: elf_sha256="
                         "0000000000000000000000000000000000000000000000000000000000000000\n")) _Exit(93);
        phase = 1;
    } else if (phase == 2) {
        char expected[80];
        snprintf(expected, sizeof(expected), "goose-embedded case-v1: %s\n", selected);
        if (strcmp(text, expected) || ge_stack_samples.completed != 1) _Exit(94);
        phase = 3;
    } else _Exit(95);
    return n;
}
void esp_system_abort(const char *details)
{
    int overflow = !strcmp(selected, "overflow");
    const char *expected = overflow ? "i32 overflow" : "goose_init must be called before exported functions";
    if (phase != 3 || strcmp(details, expected) || details != ge_scalar_v0_last_panic.message ||
        ge_stack_samples.completed != 1 || ge_stack_samples.before != 3000) _Exit(96);
    if (overflow) {
        if (!ge_scalar_v0_last_panic.file || ge_scalar_v0_last_panic.line <= 0) _Exit(97);
    } else if (ge_scalar_v0_last_panic.file || ge_scalar_v0_last_panic.line) _Exit(98);
    puts("host fatal application boundary verified");
    fflush(stdout);
    _Exit(1);
}
int main(int argc, char **argv)
{
    if (argc != 2 || (strcmp(argv[1], "cold-export") && strcmp(argv[1], "overflow"))) return 2;
    selected = argv[1];
    app_main();
    return 99;
}

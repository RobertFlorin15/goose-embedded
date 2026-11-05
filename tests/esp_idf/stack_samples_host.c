/* Executes the actual app_main using deterministic SDK and Goose doubles.
 * Numbers here are test inputs, never target measurements. */
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include "ge_leaf.h"
#include "stack_samples.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_rom_sys.h"
#include "esp_app_desc.h"

void app_main(void);
static unsigned scans, prints, step;
static int wrong_result;
static const unsigned readings[] = {3000, 2800, 2400, 2300};
static int descriptor_seen;
static const esp_app_desc_t description = {.app_elf_sha256 = {
    0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
    0x10, 0x32, 0x54, 0x76, 0x98, 0xba, 0xdc, 0xfe,
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}};

static void require(int condition) { if (!condition) _Exit(90); }

UBaseType_t uxTaskGetStackHighWaterMark(TaskHandle_t task)
{
    require(task == NULL && scans < 4 && ge_stack_samples.completed == scans);
    require((scans == 0 && step == 0 && prints == 1) || (scans == 1 && step == 3) ||
            (scans == 2 && prints == 2) || (scans == 3 && prints == 3));
    return readings[scans++];
}
void goose_init(int argc, char **argv) {
    require(argc == 0 && argv == NULL && scans == 1 && step == 0); step = 1;
}
gs_i32 ge_add(gs_i32 a, gs_i32 b) {
    require(step == 1 && a == 10 && b == 32); step = 2;
    return wrong_result ? 41 : 42;
}
void goose_exit(void) { require(step == 2 && scans == 1); step = 3; }
void ge_scalar_v0_panic_v1(const char *message, const char *file, int line) {
    require(wrong_result && !strcmp(message, "unexpected scalar result") && file && line > 0);
    require(scans == 1 && prints == 1 && step == 2 && ge_stack_samples.completed == 1);
    _Exit(1);
}
const esp_app_desc_t *esp_app_get_description(void)
{
    require(!scans && !prints && !step && ge_stack_samples.completed == 0);
    descriptor_seen = 1;
    return &description;
}
int esp_rom_printf(const char *format, ...)
{
    va_list ap;
    va_start(ap, format);
    if (prints == 0) {
        require(descriptor_seen && !step && !scans && ge_stack_samples.completed == 0);
        require(!strcmp(format, "goose-embedded identity-v1: elf_sha256=%s\n"));
        require(!strcmp(va_arg(ap, char *),
                        "0123456789abcdef1032547698badcfe000102030405060708090a0b0c0d0e0f"));
    } else if (prints == 1) {
        require(step == 3);
        require(scans == 2 && ge_stack_samples.completed == 2);
        require(!strcmp(format, "goose-embedded scalar-v0: %d\n") && va_arg(ap, int) == 42);
    } else if (prints == 2) {
        require(step == 3 && scans == 3 && ge_stack_samples.completed == 3);
        require(!strcmp(format, "goose-embedded stack-v1: before=%u after_goose=%u after_result_print=%u bytes\n"));
        for (unsigned i = 0; i < 3; ++i) require(va_arg(ap, unsigned int) == readings[i]);
    } else {
        require(prints == 3 && step == 3 && scans == 4 && ge_stack_samples.completed == 4);
        require(!strcmp(format, "goose-embedded completed-v1\n"));
    }
    ++prints;
    va_end(ap);
    return 1;
}
int main(int argc, char **argv)
{
    require(argc == 2);
    wrong_result = !strcmp(argv[1], "wrong-result");
    require(wrong_result || !strcmp(argv[1], "success"));
    /* A second invocation verifies that completed is reset before scanning. */
    for (unsigned i = 0; i < 2; ++i) {
        scans = prints = step = 0; descriptor_seen = 0;
        app_main();
        require(!wrong_result && scans == 4 && prints == 4 && step == 3);
        require(ge_stack_samples.completed == 4 && ge_stack_samples.before == readings[0] &&
                ge_stack_samples.after_goose == readings[1] &&
                ge_stack_samples.after_result_print == readings[2] &&
                ge_stack_samples.after_report == readings[3]);
    }
    return 0;
}

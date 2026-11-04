/* Tests the real platform adapter with a terminating host SDK double. */
#include "ge_leaf.h"
#include "scalar_panic.h"
#include "esp_system.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static const char *expected_message;
static const char *expected_file;
static int expected_line;
static int arithmetic;

void esp_system_abort(const char *details)
{
    if (details != ge_scalar_v0_last_panic.message) _Exit(90);
    if (expected_message && strcmp(details, expected_message)) _Exit(91);
    if (arithmetic) {
        if (!ge_scalar_v0_last_panic.file || ge_scalar_v0_last_panic.line <= 0) _Exit(92);
    } else if (ge_scalar_v0_last_panic.file != expected_file ||
               ge_scalar_v0_last_panic.line != expected_line) {
        _Exit(93);
    }
    static const char text[] = "host panic boundary verified\n";
    if (write(STDOUT_FILENO, text, sizeof(text) - 1) != sizeof(text) - 1) _Exit(94);
    _Exit(1);  /* Never return or re-enter Goose after panic. */
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (!strcmp(argv[1], "direct")) {
        expected_message = "test panic";
        expected_file = "test.goose";
        expected_line = 17;
        ge_scalar_v0_panic_v1(expected_message, expected_file, expected_line);
    }
    if (!strcmp(argv[1], "cold")) {
        expected_message = "goose_init must be called before exported functions";
        (void)ge_add(10, 32);
    }
    if (!strcmp(argv[1], "bad-init")) {
        expected_message = "invalid initialization arguments";
        goose_init(1, NULL);
    }
    goose_init(0, NULL);
    if (!strcmp(argv[1], "overflow")) {
        expected_message = "i32 overflow";
        arithmetic = 1;
        (void)ge_add(INT32_MAX, 1);
    }
    if (ge_add(10, 32) != 42 || ge_add(-10, -32) != -42) return 3;
    goose_exit();
    if (!strcmp(argv[1], "after-exit")) {
        expected_message = "goose_init must be called before exported functions";
        (void)ge_add(1, 2);
    }
    if (strcmp(argv[1], "success")) return 4;
    goose_init(0, NULL);
    if (ge_add(0, 42) != 42) return 5;
    goose_exit();
    return 0;
}

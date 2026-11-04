#include "accepted.h"
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef GE_OBSERVE
#include "runtime_observer.h"
#else
static void ge_observer_reset(void) {}
static int ge_observer_quiet(void) { return 1; }
static void ge_observer_report(const char *phase) { puts(phase); }
#endif

static void phase(const char *name) {
    if (!ge_observer_quiet()) { fputs("unexpected runtime dependency\n", stderr); _Exit(95); }
    ge_observer_report(name);
}
int main(int argc, char **argv) {
    ge_observer_reset();
    if (argc == 2) {
        const char *mode = argv[1];
        if (!strcmp(mode, "before-init")) return ge_compute(9, 2);
        if (!strcmp(mode, "bad-argc")) { goose_init(1, NULL); return 96; }
        if (!strcmp(mode, "bad-argv")) {
            char *args[] = { "unused", NULL };
            goose_init(0, args); return 96;
        }
        goose_init(0, NULL);
        if (!strcmp(mode, "after-exit")) { goose_exit(); return ge_compute(9, 2); }
        if (!strcmp(mode, "bad-ready-args")) { goose_init(-1, NULL); return 96; }
        if (!strcmp(mode, "overflow")) return ge_compute(INT32_MAX, -1);
        if (!strcmp(mode, "mul-overflow")) return ge_compute(1073741826, 2);
        if (!strcmp(mode, "add-overflow")) return ge_compute(1073741825, 2);
        if (!strcmp(mode, "neg-overflow")) return ge_compute(INT32_MIN, 0);
        return 97;
    }
    goose_exit(); phase("exit-before-init");
    for (int cycle = 0; cycle < 2; ++cycle) {
        ge_observer_reset(); goose_init(0, NULL); phase("init");
        ge_observer_reset(); goose_init(0, NULL); phase("repeat-init");
        ge_observer_reset();
        if (ge_compute(9, 2) != 23 || ge_compute(2, 9) != 9 ||
            ge_compute(0, 2) != 2 || ge_three() != 3 || ge_min() != INT32_MIN) return 98;
        phase("export");
        ge_observer_reset(); goose_exit(); phase("exit");
        ge_observer_reset(); goose_exit(); phase("repeat-exit");
    }
    return 0;
}

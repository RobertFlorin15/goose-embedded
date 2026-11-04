#include "leaf.h"
#include "runtime_observer.h"
#include <string.h>

int main(int argc, char **argv) {
    /* These two modes must fail in the runtime, in separate processes. */
    if (argc == 2 && !strcmp(argv[1], "before-init")) return ge_add(20, 22);
    if (argc == 2 && !strcmp(argv[1], "after-exit")) {
        goose_init(0, 0);
        goose_exit();
        return ge_add(20, 22);
    }
    if (argc == 2 && !strcmp(argv[1], "overflow")) {
        goose_init(0, 0);
        return ge_add(INT32_MAX, 1);
    }
    ge_observer_reset();
    goose_exit();
    if (!ge_observer_quiet()) return 10;
    ge_observer_report("exit-before-init");
    for (int i = 0; i < 2; ++i) {
        ge_observer_reset();
        goose_init(0, 0);
        ge_observer_report("init");
        ge_observer_reset();
        goose_init(0, 0);
        if (!ge_observer_quiet()) return 11;
        ge_observer_report("repeat-init");
        ge_observer_reset();
        if (ge_add(19, 23) != 42) return 12;
        if (!ge_observer_quiet()) return 13;
        ge_observer_report("export");
        ge_observer_reset();
        goose_exit();
        ge_observer_report("exit");
        ge_observer_reset();
        goose_exit();
        if (!ge_observer_quiet()) return 14;
        ge_observer_report("repeat-exit");
    }
    return 0;
}

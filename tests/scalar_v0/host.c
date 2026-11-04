#include "accepted.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
int main(int argc, char **argv) {
    goose_init(0, NULL);
    if (argc > 1 && !strcmp(argv[1], "overflow")) return ge_compute(INT32_MAX, -1);
    if (argc > 1 && !strcmp(argv[1], "mul-overflow")) return ge_compute(1073741826, 2);
    if (argc > 1 && !strcmp(argv[1], "add-overflow")) return ge_compute(1073741825, 2);
    if (argc > 1 && !strcmp(argv[1], "neg-overflow")) return ge_compute(INT32_MIN, 0);
    if (ge_compute(9, 2) != 23 || ge_compute(2, 9) != 9 ||
        ge_compute(0, 2) != 2 || ge_three() != 3 || ge_min() != INT32_MIN) return 1;
    goose_exit();
    goose_init(0, NULL);
    if (ge_compute(9, 2) != 23) return 2;
    goose_exit();
    puts("scalar-v0 validator: host semantics pass (desktop runtime)");
    return 0;
}

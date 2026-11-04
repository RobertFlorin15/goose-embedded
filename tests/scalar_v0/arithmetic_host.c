#include "arithmetic.h"
#include "runtime_observer.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc != 4) return 90;
    int32_t a = (int32_t)strtoll(argv[2], NULL, 10);
    int32_t b = (int32_t)strtoll(argv[3], NULL, 10);
    const char *op = argv[1];
    ge_observer_reset();
    goose_init(0, NULL);
    int32_t result;
    if (!strcmp(op, "add")) result = ge_add(a, b);
    else if (!strcmp(op, "sub")) result = ge_sub(a, b);
    else if (!strcmp(op, "mul")) result = ge_mul(a, b);
    else if (!strcmp(op, "neg")) result = ge_neg(a);
    else return 90;
    goose_exit();
    if (!ge_observer_quiet()) return 93;
    printf("%" PRId32 "\n", result);
    return 0;
}

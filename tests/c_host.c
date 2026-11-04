#ifndef GE_HEADER
#define GE_HEADER "scalar.h"
#endif
#include GE_HEADER
#include <stdio.h>
int main(void) {
    for (int i = 0; i < 2; ++i) {
        goose_init(0, NULL);
        if (ge_add(19, 23) != 42) return 1;
        goose_exit();
    }
    puts("c-host: 42; restarted twice");
    return 0;
}

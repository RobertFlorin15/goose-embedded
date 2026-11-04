#ifndef GE_ESP_IDF_SCALAR_PANIC_H
#define GE_ESP_IDF_SCALAR_PANIC_H

/* Debugger-visible borrowed static strings. Valid after fatal error until reset.
 * Single serial task caller only; this is not a concurrent crash recorder. */
struct ge_scalar_v0_panic_record {
    const char *message;
    const char *file;
    int line;
};
extern volatile struct ge_scalar_v0_panic_record ge_scalar_v0_last_panic;

#endif

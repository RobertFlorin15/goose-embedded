#ifndef GE_EXAMPLE_STACK_SAMPLES_H
#define GE_EXAMPLE_STACK_SAMPLES_H
#include <stdint.h>

/* Current main task's lifetime low-water readings, in bytes. No hardware
 * readings exist until this application actually runs. Debugger-visible only;
 * not atomic, retained across reset, or a worst-case stack-bound certificate. */
struct ge_example_stack_samples {
    uint32_t before;
    uint32_t after_goose;
    uint32_t after_result_print;
    uint32_t after_report;
    uint32_t completed;
};
extern volatile struct ge_example_stack_samples ge_stack_samples;
#endif

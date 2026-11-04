#ifndef GE_RUNTIME_OBSERVER_H
#define GE_RUNTIME_OBSERVER_H
/* Observes direct linker-wrapped calls, not libc's internal activity. */
void ge_observer_reset(void);
int ge_observer_quiet(void);
void ge_observer_report(const char *phase);
#endif

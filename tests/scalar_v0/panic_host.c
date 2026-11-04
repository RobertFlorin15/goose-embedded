/* Host-only platform binding. No allocator or formatted diagnostics. */
#ifndef GE_PROFILE_HEADER
#define GE_PROFILE_HEADER "accepted.h"
#endif
#include GE_PROFILE_HEADER
#include <stdlib.h>
#include <unistd.h>
#ifdef GE_OBSERVE
#include "runtime_observer.h"
#endif
#if GE_SCALAR_V0_ABI_VERSION != 1
#error "host panic adapter requires scalar ABI 1"
#endif
static void text(const char *s) {
    if (!s) return;
    size_t n = 0;
    while (s[n]) ++n;
    while (n) {
        ssize_t done = write(STDERR_FILENO, s, n);
        if (done <= 0) _Exit(92);
        s += done;
        n -= (size_t)done;
    }
}
void ge_scalar_v0_panic_v1(const char *message, const char *file, int line) {
#ifdef GE_OBSERVE
    if (!ge_observer_quiet()) _Exit(93);
#endif
    /* Arithmetic errors carry source location, lifecycle errors use NULL/0. */
    if ((file && line <= 0) || (!file && line != 0)) _Exit(94);
    text("scalar panic: "); text(message); text("\n");
    if (file) { text("source: "); text(file); text("\n"); }
    _Exit(1);
}

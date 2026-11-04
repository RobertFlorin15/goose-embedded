#define _GNU_SOURCE
#include <signal.h>
#include <pthread.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>
#include "runtime_observer.h"

enum { CALLOC, MALLOC, FREE, SYSCONF, SIGACTION, SIGALTSTACK,
       MMAP, MPROTECT, MUNMAP, THREAD_ATTR, THREAD_STACK, THREAD_ATTR_DESTROY,
       MUTEX_LOCK, MUTEX_UNLOCK, CALL_COUNT };
static unsigned long calls[CALL_COUNT];
static const char *names[CALL_COUNT] = {
    "calloc", "malloc", "free", "sysconf", "sigaction", "sigaltstack",
    "mmap", "mprotect", "munmap", "pthread_getattr_np", "pthread_attr_getstack",
    "pthread_attr_destroy", "pthread_mutex_lock", "pthread_mutex_unlock"
};
void ge_observer_reset(void) {
    for (int i = 0; i < CALL_COUNT; ++i) calls[i] = 0;
}
int ge_observer_quiet(void) {
    for (int i = 0; i < CALL_COUNT; ++i) if (calls[i]) return 0;
    return 1;
}
void ge_observer_report(const char *phase) {
    /* Snapshot before reporting; stdio is outside the observed phase. */
    unsigned long snapshot[CALL_COUNT];
    for (int i = 0; i < CALL_COUNT; ++i) snapshot[i] = calls[i];
    printf("{\"phase\":\"%s\",\"calls\":{", phase);
    for (int i = 0; i < CALL_COUNT; ++i)
        printf("%s\"%s\":%lu", i ? "," : "", names[i], snapshot[i]);
    puts("}}");
}

void *__real_calloc(size_t, size_t);
void *__wrap_calloc(size_t n, size_t s) { ++calls[CALLOC]; return __real_calloc(n, s); }
void *__real_malloc(size_t);
void *__wrap_malloc(size_t s) { ++calls[MALLOC]; return __real_malloc(s); }
void __real_free(void *);
void __wrap_free(void *p) { ++calls[FREE]; __real_free(p); }
long __real_sysconf(int);
long __wrap_sysconf(int n) { ++calls[SYSCONF]; return __real_sysconf(n); }
int __real_sigaction(int, const struct sigaction *, struct sigaction *);
int __wrap_sigaction(int n, const struct sigaction *a, struct sigaction *b) {
    ++calls[SIGACTION]; return __real_sigaction(n, a, b);
}
int __real_sigaltstack(const stack_t *, stack_t *);
int __wrap_sigaltstack(const stack_t *a, stack_t *b) {
    ++calls[SIGALTSTACK]; return __real_sigaltstack(a, b);
}
void *__real_mmap(void *, size_t, int, int, int, off_t);
void *__wrap_mmap(void *p, size_t s, int prot, int flags, int fd, off_t offset) {
    ++calls[MMAP]; return __real_mmap(p, s, prot, flags, fd, offset);
}
int __real_mprotect(void *, size_t, int);
int __wrap_mprotect(void *p, size_t s, int prot) {
    ++calls[MPROTECT]; return __real_mprotect(p, s, prot);
}
int __real_munmap(void *, size_t);
int __wrap_munmap(void *p, size_t s) { ++calls[MUNMAP]; return __real_munmap(p, s); }
int __real_pthread_getattr_np(pthread_t, pthread_attr_t *);
int __wrap_pthread_getattr_np(pthread_t t, pthread_attr_t *a) {
    ++calls[THREAD_ATTR]; return __real_pthread_getattr_np(t, a);
}
int __real_pthread_attr_getstack(const pthread_attr_t *, void **, size_t *);
int __wrap_pthread_attr_getstack(const pthread_attr_t *a, void **p, size_t *s) {
    ++calls[THREAD_STACK]; return __real_pthread_attr_getstack(a, p, s);
}
int __real_pthread_attr_destroy(pthread_attr_t *);
int __wrap_pthread_attr_destroy(pthread_attr_t *a) {
    ++calls[THREAD_ATTR_DESTROY]; return __real_pthread_attr_destroy(a);
}
int __real_pthread_mutex_lock(pthread_mutex_t *);
int __wrap_pthread_mutex_lock(pthread_mutex_t *m) {
    ++calls[MUTEX_LOCK]; return __real_pthread_mutex_lock(m);
}
int __real_pthread_mutex_unlock(pthread_mutex_t *);
int __wrap_pthread_mutex_unlock(pthread_mutex_t *m) {
    ++calls[MUTEX_UNLOCK]; return __real_pthread_mutex_unlock(m);
}

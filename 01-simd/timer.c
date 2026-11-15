#define _GNU_SOURCE
#include <stdint.h>
#include <stddef.h>
#include <time.h>
#include <x86intrin.h>
typedef void (*kernel)(size_t,size_t,void*,void*,void*);
double measure(kernel fn, size_t n, size_t stride, void *x, void *y, void *z, int repeats, uint64_t *ticks) {
    struct timespec a,b;
    unsigned aux;
    clock_gettime(CLOCK_MONOTONIC_RAW,&a);
    uint64_t start=__rdtscp(&aux);
    _mm_lfence();
    for(int r=0;r<repeats;r++) fn(n,stride,x,y,z);
    *ticks=__rdtscp(&aux)-start;
    clock_gettime(CLOCK_MONOTONIC_RAW,&b);
    return b.tv_sec-a.tv_sec+(b.tv_nsec-a.tv_nsec)*1e-9;
}

// Build once per precision and ISA. RESTRICT allows independent array streams.
#include <stddef.h>
#ifndef REAL
#define REAL float
#endif
#define PARAMS size_t n, size_t stride, const REAL *restrict x, REAL *restrict y, REAL *restrict z
void multiply(PARAMS) {
    if (stride == 1) {
        for (size_t i=0;i<n;i++) z[i]=x[i]*y[i];
    } else {
        for (size_t i=0;i<n;i++) z[i*stride]=x[i*stride]*y[i*stride];
    }
}
void axpy(PARAMS) {
    (void)z;
    REAL *out=(REAL *)y; // caller supplies writable y
    if (stride == 1) {
        for (size_t i=0;i<n;i++) out[i]=(REAL)0.25*x[i]+out[i];
    } else {
        for (size_t i=0;i<n;i++) out[i*stride]=(REAL)0.25*x[i*stride]+out[i*stride];
    }
}
void stencil(PARAMS) {
    (void)y; (void)stride;
    for (size_t i=0;i<n;i++) z[i]=((REAL)0.25*x[i]+(REAL)0.5*x[i+1])+(REAL)0.25*x[i+2];
}
void copy_stream(PARAMS) {
    (void)y; (void)stride;
    for (size_t i=0;i<n;i++) z[i]=x[i];
}

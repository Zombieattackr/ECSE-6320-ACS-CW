// Optional hardware events around the timed elementwise-multiply region only.
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <linux/perf_event.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
static int open_event(unsigned type,unsigned long long config) {
    struct perf_event_attr a={.type=type,.size=sizeof a,.config=config,.exclude_kernel=1,.exclude_hv=1};
    return syscall(SYS_perf_event_open,&a,0,-1,-1,0);
}
static long long read_event(int fd){
    long long value;return fd>=0 && read(fd,&value,sizeof value)==sizeof value?value:-1;
}
static double now(void) {
    struct timespec t;clock_gettime(CLOCK_MONOTONIC_RAW,&t);return t.tv_sec+t.tv_nsec*1e-9;
}
__attribute__((noinline)) static void multiply(float *restrict z,const float *restrict x,const float *restrict y,int n,int step) {
    for(int i=0;i<n;i+=step)z[i]=x[i]*y[i];
}
int main(int argc,char **argv){
    if(argc!=3)return 1;
    int n=atoi(argv[1]),step=atoi(argv[2]);assert(n>0 && step>0);
    float *x=malloc(n*sizeof *x),*y=malloc(n*sizeof *y),*z=calloc(n,sizeof *z);assert(x && y && z);
    for(int i=0;i<n;i++){x[i]=i%7;y[i]=i%11;}
    multiply(z,x,y,n,step);
    int fd[4],err[4];long long start[4];
    unsigned type[]={PERF_TYPE_HARDWARE,PERF_TYPE_HARDWARE,PERF_TYPE_HARDWARE,PERF_TYPE_HW_CACHE};
    unsigned config[]={PERF_COUNT_HW_CPU_CYCLES,PERF_COUNT_HW_INSTRUCTIONS,PERF_COUNT_HW_CACHE_MISSES,
        PERF_COUNT_HW_CACHE_DTLB|(PERF_COUNT_HW_CACHE_OP_READ<<8)|(PERF_COUNT_HW_CACHE_RESULT_MISS<<16)};
    for(int k=0;k<4;k++){fd[k]=open_event(type[k],config[k]);err[k]=fd[k]<0?errno:0;start[k]=read_event(fd[k]);}
    double a=now();int passes=0;
    do{multiply(z,x,y,n,step);__asm__ volatile("" ::: "memory");passes++;}while(now()-a<.05);
    double seconds=now()-a;
    printf("%d,%d,%d,%.9f",n,step,passes,seconds);
    for(int k=0;k<4;k++){long long end=read_event(fd[k]);printf(",%lld,%d",end<0||start[k]<0?-1:end-start[k],err[k]);}
    for(int i=0;i<n;i++)assert(z[i]==(i%step==0?x[i]*y[i]:0));
    puts("");
}

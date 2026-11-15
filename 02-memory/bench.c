#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <inttypes.h>
#include <linux/perf_event.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#include <cpuid.h>

static double now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC_RAW,&t);
    return t.tv_sec+t.tv_nsec*1e-9;
}
static uint32_t rng(uint32_t *state) {
    uint32_t x=*state; x^=x<<13; x^=x>>17; x^=x<<5; return *state=x;
}
static int cpu[CPU_SETSIZE], ncpu;
static void pin(int n) {
    cpu_set_t c; CPU_ZERO(&c); CPU_SET(cpu[n%ncpu],&c);
    if(sched_setaffinity(0,sizeof c,&c)) {perror("pin");exit(2);}
}
static void *region(size_t bytes,int huge) {
    void *p=mmap(0,bytes,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(p==MAP_FAILED){perror("mmap");exit(2);}
    if(madvise(p,bytes,huge?MADV_HUGEPAGE:MADV_NOHUGEPAGE)) perror("madvise");
    return p;
}
static long huge_kb(void *ptr) {
    FILE *f=fopen("/proc/self/smaps","r"); if(!f)return -1;
    char buf[512];uintptr_t lo,hi; int found=0;long kb=-1;
    while(fgets(buf,sizeof buf,f)) {
        if(sscanf(buf,"%"SCNxPTR"-%"SCNxPTR,&lo,&hi)==2) found=(uintptr_t)ptr>=lo && (uintptr_t)ptr<hi;
        if(found && sscanf(buf,"AnonHugePages: %ld",&kb)==1) break;
    }
    fclose(f);return kb;
}
static void cycle(uint8_t *p,size_t bytes,int stride,int random,uint32_t seed) {
    unsigned n=bytes/stride;
    unsigned *perm=malloc(n*sizeof *perm);assert(perm);
    for(unsigned i=0;i<n;i++) perm[i]=i;
    if(random) for(unsigned i=n-1;i;i--) {
        unsigned j=rng(&seed)%(i+1),t=perm[j];perm[j]=perm[i];perm[i]=t;
    }
    for(unsigned i=0;i<n;i++) *(uint32_t*)(p+(size_t)perm[i]*stride)=perm[(i+1)%n]*stride;
    uint32_t current=0;
    for(unsigned i=1;i<=n;i++) {
        current=*(uint32_t*)(p+current);
        assert((current==0)==(i==n));
    }
    free(perm);
}
static uint32_t chase(uint8_t *p,uint32_t pos,unsigned n) {
    while(n--)pos=*(uint32_t*)(p+pos);
    return pos;
}
static atomic_int ready,go,stop;
typedef struct {int id,pct,stride,random;size_t bytes; uint64_t ops,sum;} Worker;
static void *stream(void *arg) {
    Worker *w=arg; pin(w->id);unsigned slots=w->bytes/w->stride;
    uint8_t *p=region(w->bytes,0); memset(p,1,w->bytes);
    unsigned at=0,state=123+w->id;uint64_t sum=0;
    // A shuffled index array gives identical address-order overhead for all mixes.
    unsigned *offset=malloc(slots*sizeof *offset);assert(offset);
    for(unsigned i=0;i<slots;i++)offset[i]=i*w->stride;
    if(w->random)for(unsigned i=slots-1;i;i--){
        unsigned j=rng(&state)%(i+1),v=offset[j];offset[j]=offset[i];offset[i]=v;
    }
    atomic_fetch_add(&ready,1);while(!atomic_load(&go))sched_yield();
    uint64_t ops=0;
    while(!atomic_load(&stop)){
        for(int i=0;i<1000;i++) {
            volatile uint64_t *v=(void*)(p+offset[at]);
            if(i%100<w->pct)sum+=*v;else *v=(uint64_t)i;
            if(++at==slots)at=0;
        }
        ops+=1000;
    }
    w->ops=ops;w->sum=sum;free(offset);munmap(p,w->bytes);return NULL;
}
static int counter(unsigned type,uint64_t config) {
    struct perf_event_attr a={.type=type,.size=sizeof a,.config=config,.exclude_kernel=1,.exclude_hv=1};
    return syscall(SYS_perf_event_open,&a,0,-1,-1,0);
}
static long long count(int fd) {
    long long v;return fd>=0 && read(fd,&v,8)==8?v:-1;
}
int main(int argc,char **argv) {
    if(argc==2 && !strcmp(argv[1],"cache")) {
        unsigned a,b,c,d;
        for(int i=0;i<16;i++) {
            __cpuid_count(4,i,a,b,c,d);if(!(a&31))break;
            printf("level %u type %u bytes %llu line %u\n",(a>>5)&7,a&31,
            (unsigned long long)((b>>22)+1)*(((b>>12)&1023)+1)*((b&4095)+1)*((uint64_t)c+1),(b&4095)+1);
        } return 0;
    }
    if(argc!=10 && argc!=11)return 1;
    size_t bytes=strtoull(argv[1],0,10);int stride=atoi(argv[2]),random=atoi(argv[3]),workers=atoi(argv[4]);
    int pct=atoi(argv[5]),huge=atoi(argv[6]),seed=atoi(argv[7]),ws=atoi(argv[8]),wr=atoi(argv[9]);
    cpu_set_t set;sched_getaffinity(0,sizeof set,&set);
    for(int i=0;i<CPU_SETSIZE;i++)if(CPU_ISSET(i,&set))cpu[ncpu++]=i;
    if(workers>=ncpu){fprintf(stderr,"insufficient CPUs\n");return 2;}pin(0);
    uint8_t *p=region(bytes,huge);cycle(p,bytes,stride,random,seed);
    long hk=huge_kb(p);
    Worker w[16];pthread_t tid[16];
    for(int i=0;i<workers;i++){
        w[i]=(Worker){.id=i+1,.pct=pct,.stride=ws,.random=wr,.bytes=67108864};
        assert(pthread_create(tid+i,NULL,stream,w+i)==0);
    }
    while(atomic_load(&ready)<workers)sched_yield();
    int chains=argc==11?atoi(argv[10]):1;
    assert(chains>=1 && chains<=16);
    uint32_t heads[16];for(int i=0;i<chains;i++)heads[i]=(bytes/stride/chains*i)*stride;
    int cm=counter(PERF_TYPE_HARDWARE,PERF_COUNT_HW_CACHE_MISSES);
    int err=cm<0?errno:0;
    int tm=counter(PERF_TYPE_HW_CACHE,PERF_COUNT_HW_CACHE_DTLB|(PERF_COUNT_HW_CACHE_OP_READ<<8)|(PERF_COUNT_HW_CACHE_RESULT_MISS<<16));
    long long c0=count(cm),t0=count(tm);
    size_t loads=0;
    double start=now();atomic_store(&go,1);
    do{
        if(chains==1) heads[0]=chase(p,heads[0],4096);
        else {
            for(unsigned step=0;step<4096u/chains;step++)
                for(int i=0;i<chains;i++) heads[i]=*(uint32_t*)(p+heads[i]);
        }
        loads+=4096;
    }while(now()-start<0.080);
    atomic_store(&stop,1);double elapsed=now()-start;
    long long c1=count(cm),t1=count(tm);uint64_t ops=0,checksum=0;for(int i=0;i<chains;i++)checksum+=heads[i];
    for(int i=0;i<workers;i++){pthread_join(tid[i],NULL);ops+=w[i].ops;checksum+=w[i].sum;}
    printf("%.9f,%zu,%"PRIu64",%ld,%lld,%lld,%d,%"PRIu64"\n",elapsed,loads,ops,hk,c0<0?-1:c1-c0,t0<0?-1:t1-t0,err,checksum);
}

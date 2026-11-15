#include <stdint.h>
#include <cpuid.h>
#include <stdio.h>
int main(void) {
unsigned a,b,c,d;
        for(int i=0;i<16;i++) {
            __cpuid_count(4,i,a,b,c,d);if(!(a&31))break;
            printf("level %u type %u bytes %llu line %u\n",(a>>5)&7,a&31,
            (unsigned long long)((b>>22)+1)*(((b>>12)&1023)+1)*((b&4095)+1)*((uint64_t)c+1),(b&4095)+1);
        } return 0;
    }

import os,random,subprocess
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
subprocess.run(['gcc','-O3','-march=native','-Wall','counters.c','-o','build/counters'],check=True)
with open('raw/kernel_counters.csv','w') as out:
    out.write('trial,n,stride,passes,seconds,cycles,cycles_errno,instructions,instructions_errno,cache_misses,cache_errno,dtlb_misses,dtlb_errno\n')
    for rep in range(3):
        order=[(1024,1),(262144,1),(50331648,1),(50331648,16),(50331648,1024)]
        random.Random(888+rep).shuffle(order)
        for n,s in order:out.write(str(rep)+','+subprocess.check_output(['build/counters',str(n),str(s)],text=True))

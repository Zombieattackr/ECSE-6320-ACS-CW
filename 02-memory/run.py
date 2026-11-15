import csv,os,random,subprocess
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
subprocess.run(['bash','build.sh'],check=True)
with open('raw/environment.txt','w') as f: subprocess.run(['bash','environment.sh'],stdout=f,check=True)
with open('raw/cache.txt','w') as f: subprocess.run(['build/bench','cache'],stdout=f,check=True)
cases=set()
def add(kib,stride=64,rand=1,workers=0,pct=100,huge=0,ws=64,wr=0,chains=1):
    cases.add((kib*1024,stride,rand,workers,pct,huge,ws,wr,chains))
for kib in [8,32,64,256,1024,2048,4096,16384,65536,262144,524288]: add(kib)
for stride in [64,256,1024,4096]:
    for rand in [0,1]: add(524288,stride,rand)
for huge in [0,1]:
    for stride in [64,4096]: add(65536,stride,huge=huge)
for chains in [2,4,8,16]:add(524288,chains=chains)
available=len(os.sched_getaffinity(0))-1
for workers in [1,2,3,4,6,8]:
    if workers<=available:add(524288,workers=workers)
if available:
    for ws in [64,256,1024]:
        for wr in [0,1]:add(524288,workers=1,ws=ws,wr=wr)
    for pct in [0,50,70,100]:add(524288,workers=min(4,available),pct=pct)
with open('raw/trials.csv','w',buffering=1) as f:
    w=csv.writer(f);w.writerow('bytes stride random workers read_pct huge_hint stream_stride stream_random chains trial seconds loads stream_ops huge_kib cache_misses dtlb_misses perf_errno checksum'.split())
    for rep in range(3):
        order=sorted(cases);random.Random(913+rep).shuffle(order)
        for size,s,r,n,p,h,ws,wr,chains in order:
            cmd=['build/bench',size,s,r,n,p,h,rep+141,ws,wr,chains]
            row=subprocess.check_output(list(map(str,cmd)),text=True).strip().split(',')
            w.writerow([size,s,r,n,p,h,ws,wr,chains,rep,*row])
subprocess.run(['python3','counter_run.py'],check=True)

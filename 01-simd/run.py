"""Single pinned caller. Each trial is a separately initialized working set."""
import csv, ctypes as C, os, random, subprocess
from pathlib import Path
import numpy as np
os.chdir(Path(__file__).resolve().parent)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
# Capture cache boundaries for this CPU with the same CPUID query as the memory lab.
subprocess.run(['gcc','-O2','cache.c','-o','raw/cache-probe'],check=True)
try:
    with open('raw/cache.txt','w') as output:
        subprocess.run(['./raw/cache-probe'],stdout=output,check=True)
finally:
    Path('raw/cache-probe').unlink(missing_ok=True)
subprocess.run(['bash','build.sh'],check=True)
subprocess.run(['bash','environment.sh'],stdout=open('raw/environment.txt','w'),check=True)
timer=C.CDLL('./build/timer.so').measure
ptr=C.c_void_p
timer.argtypes=[ptr,C.c_size_t,C.c_size_t,ptr,ptr,ptr,C.c_int,C.POINTER(C.c_uint64)]
timer.restype=C.c_double
def allocate(n,dt,shift):
    buf=np.empty(n+80,dt)
    off=(-buf.ctypes.data % 64)//buf.itemsize+shift
    return buf[off:off+n]
cases=set()
for dt in ['float','double']:
    for k in ['multiply','axpy','stencil']:
        for n in [512,8192,65536,524288,4194304,50331648]:
            for v in ['scalar','default','native']:
                cases.add((k,dt,n,1,0,v))
for n in [64,67,65536,65539]:
    for sh in [0,1]:
        for v in ['scalar','native']:
            cases.add(('multiply','float',n,1,sh,v))
for stride in [1,2,4,8]:
    for v in ['scalar','native']:
        cases.add(('multiply','float',4194304,stride,0,v))
cases.add(('copy_stream','float',50331648,1,0,'native'))
libs={}
with open('raw/trials.csv','w',buffering=1) as f:
    w=csv.writer(f); w.writerow('kernel dtype n stride shift build trial passes sec tsc_ticks footprint_B useful_B flops'.split())
    for rep in range(3):
        order=sorted(cases);random.Random(419+rep).shuffle(order)
        for k,dt,n,s,sh,v in order:
            typ=np.float32 if dt=='float' else np.float64
            size=(n-1)*s+1+(2 if k=='stencil' else 0)
            x=allocate(size,typ,sh); y=allocate(size if k in ('multiply','axpy') else 1,typ,sh)
            z=allocate(size if k!='axpy' else 1,typ,sh)
            x.fill(0.5); y.fill(1.0); z.fill(-9)
            # Vary inputs with an exactly representable sequence, including boundaries.
            x[::3]=0.25; y[::5]=2
            key=(v,dt)
            if key not in libs: libs[key]=C.CDLL('./build/%s_%s.so'%key)
            fn=getattr(libs[key],k); args=[fn,n,s,x.ctypes.data,y.ctypes.data,z.ctypes.data]
            ticks=C.c_uint64()
            idx=np.unique(np.linspace(0,n-1,min(n,1001),dtype=int))*s
            if k=='multiply': ref=x[idx]*y[idx]
            if k=='axpy': ref=.25*x[idx]+y[idx]
            if k=='stencil': ref=.25*x[idx]+.5*x[idx+1]+.25*x[idx+2]
            if k=='copy_stream': ref=x[idx]
            warm=timer(*args,1,C.byref(ticks))
            out=y if k=='axpy' else z
            np.testing.assert_array_equal(out[idx],ref)
            if s>1: assert np.all(z[1::s]==-9)
            passes=max(1,min(300000,round(.012/max(warm,1e-8))))
            sec=timer(*args,passes,C.byref(ticks))
            streams=3 if k in ('multiply','axpy') else 2
            active=3 if k=='multiply' else 2
            w.writerow([k,dt,n,s,sh,v,rep,passes,sec,ticks.value,(active*((n-1)*s+1)+(2 if k=='stencil' else 0))*x.itemsize,streams*n*x.itemsize,{'multiply':1,'axpy':2,'stencil':5,'copy_stream':0}[k]*n])
            del x,y,z,out

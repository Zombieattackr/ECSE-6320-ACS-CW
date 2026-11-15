from pathlib import Path
import os,pandas as pd, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
os.chdir(Path(__file__).resolve().parent)
cache_levels = {}
for line in Path('raw/cache.txt').read_text().splitlines():
    fields = line.split()
    if fields[3] in ('1','3'):
        cache_levels[int(fields[1])] = int(fields[5]) / 2**20
r=pd.read_csv('raw/trials.csv');r['MiB']=r.bytes/2**20
r['ns']=r.seconds*1e9/r.loads
r['lookups_Ms']=r.loads/r.seconds/1e6
r['stream_MiBs']=r.stream_ops*8/r.seconds/2**20
r['pointer_MiBs']=r.loads*4/r.seconds/2**20
r['chain_cycle_ns']=r.chains*r.ns
r.to_csv('processed/individual.csv',index=False)
keys=['MiB','stride','random','workers','read_pct','huge_hint','stream_stride','stream_random','chains']
g=r.groupby(keys).agg(ns=('ns','median'),lo=('ns','min'),hi=('ns','max'),Mops=('lookups_Ms','median'),stream_MiBs=('stream_MiBs','median'),stream_lo=('stream_MiBs','min'),stream_hi=('stream_MiBs','max'),pointer_MiBs=('pointer_MiBs','median'),chain_cycle_ns=('chain_cycle_ns','median'),huge_kib=('huge_kib','median'),trials=('trial','size')).reset_index()
assert (g.trials==3).all()
g.to_csv('processed/summary.csv',index=False)
base=g.query('workers==0 and random==1 and huge_hint==0 and chains==1 and stride==64').sort_values('MiB')
fig,ax=plt.subplots(1,2,figsize=(11,4.4))
def err(ax,x,y,low,high,d,label=None):
    ax.errorbar(d[x],d[y],yerr=[d[y]-d[low],d[high]-d[y]],fmt='o-',capsize=3,label=label)
err(ax[0],'MiB','ns','lo','hi',base)
for cap,label in [(cache_levels[n], label) for n,label in [(1,'L1D'),(2,'L2'),(3,'LLC')] if n in cache_levels]:
    ax[0].axvline(cap,ls=':',c='gray');ax[0].text(cap,0.95,label,transform=ax[0].get_xaxis_transform(),ha='right',va='top')
ax[0].set(xscale='log',yscale='log',xlabel='Ring footprint (MiB)',ylabel='Dependent load latency (ns)',title='One random chain, one pinned CPU')
for rand in (0,1):
    d=g.query('MiB==512 and random==@rand and workers==0 and chains==1 and huge_hint==0').sort_values('stride')
    err(ax[1],'stride','ns','lo','hi',d,['sequential','shuffled'][rand])
ax[1].set(xscale='log',xlabel='Node spacing (B)',ylabel='Dependent load latency (ns)',title='Fixed 512 MiB address range');ax[1].legend()
for a in ax:a.grid(alpha=.22)
fig.tight_layout();fig.savefig('figures/hierarchy.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(11,4.4))
d=g.query('MiB==512 and stride==64 and random==1 and read_pct==100 and stream_stride==64 and stream_random==0 and chains==1').sort_values('workers')
ax[0].errorbar(d.stream_MiBs,d.ns,xerr=[d.stream_MiBs-d.stream_lo,d.stream_hi-d.stream_MiBs],yerr=[d.ns-d.lo,d.hi-d.ns],fmt='o-',capsize=3)
for t in d.itertuples():ax[0].annotate(str(t.workers),(t.stream_MiBs,t.ns),xytext=(3,4),textcoords='offset points')
ax[0].set(yscale='log',xlabel='Background useful throughput (MiB/s)',ylabel='Probe latency (ns)',title='Worker counts label each point')
d=g.query('MiB==512 and random==1 and stride==64 and workers==0 and huge_hint==0').sort_values('chains')
ax[1].plot(d.chains,d.Mops,'o-');ax[1].set(xlabel='Independent dependent-load chains',ylabel='Million lookups/s',title='Single-core memory-level parallelism')
for a in ax:a.grid(alpha=.22)
fig.tight_layout();fig.savefig('figures/intensity.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(1,3,figsize=(13,4))
d=g.query('workers==1 and MiB==512 and read_pct==100')
for rand in [0,1]:
    a=d[d.stream_random==rand].sort_values('stream_stride')
    err(ax[0],'stream_stride','stream_MiBs','stream_lo','stream_hi',a,['sequential','shuffled'][rand])
ax[0].set(xlabel='Worker node spacing (B)',ylabel='Useful MiB/s',title='One 64 MiB worker');ax[0].legend()
w=min(4,int(g.workers.max()))
d=g.query('workers==@w and stream_stride==64 and stream_random==0 and read_pct in [0,50,70,100]').sort_values('read_pct')
err(ax[1],'read_pct','stream_MiBs','stream_lo','stream_hi',d);ax[1].set(xlabel='Read share (%)',ylabel='Useful MiB/s',title=f'{w} streaming workers')
d=g.query('MiB==64 and workers==0 and chains==1 and random==1')
for hint in [0,1]:
    a=d[d.huge_hint==hint].sort_values('stride')
    err(ax[2],'stride','ns','lo','hi',a,['NOHUGEPAGE','HUGEPAGE'][hint])
ax[2].set(xlabel='Node spacing (B)',ylabel='ns per load',title='Page-policy request');ax[2].legend()
fig.tight_layout();fig.savefig('figures/patterns.png',dpi=150)
c=pd.read_csv('raw/kernel_counters.csv')
c['ns_per_product']=c.seconds*1e9/(c.passes*np.ceil(c.n/c.stride))
c.to_csv('processed/kernel_counters.csv',index=False)

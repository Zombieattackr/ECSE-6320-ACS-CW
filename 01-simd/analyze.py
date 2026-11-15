from pathlib import Path
import os, numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
os.chdir(Path(__file__).resolve().parent)
cache_levels = {}
for line in Path('raw/cache.txt').read_text().splitlines():
    fields = line.split()
    if fields[3] in ('1','3'):
        cache_levels[int(fields[1])] = int(fields[5]) / 2**20
r=pd.read_csv('raw/trials.csv')
r['ns']=r.sec*1e9/(r.passes*r.n)
r['GFLOPs']=r.flops*r.passes/r.sec/1e9
r['GiBs']=r.useful_B*r.passes/r.sec/2**30
r['ref_cycles']=r.tsc_ticks/(r.n*r.passes)
keys=['kernel','dtype','n','stride','shift','build','footprint_B']
r.to_csv('processed/individual.csv',index=False)
g=r.groupby(keys).agg(ns=('ns','median'),low=('ns','min'),high=('ns','max'),GFLOPs=('GFLOPs','median'),GiBs=('GiBs','median'),ref_cycles=('ref_cycles','median'),trials=('ns','size')).reset_index()
assert (g.trials==3).all()
g=g.merge(g[g.build=='scalar'][keys[:5]+['ns']].rename(columns={'ns':'scalar_ns'}),on=keys[:5],how='left')
g['speedup']=g.scalar_ns/g.ns
g.to_csv('processed/summary.csv',index=False)
main=g.query('stride==1 and shift==0 and n in [512,8192,65536,524288,4194304,50331648]')
fig,axs=plt.subplots(2,3,figsize=(13,6.8),sharex='col')
for col,k in enumerate(('multiply','axpy','stencil')):
    data=main.query('kernel==@k and dtype=="float"')
    for v,grp in data.groupby('build'):
        x=grp.footprint_B/2**20
        ax=axs[0,col]
        line,=ax.plot(x,grp.GFLOPs,'o-',label=v)
        ax.vlines(x,grp.GFLOPs*grp.ns/grp.high,grp.GFLOPs*grp.ns/grp.low,color=line.get_color())
        axs[1,col].plot(x,grp.speedup,'o-',label=v)
    axs[0,col].set_title(k);axs[1,col].set_xlabel('Active footprint (MiB)')
    for ax in axs[:,col]:
        ax.set_xscale('log');ax.grid(alpha=.22)
        for cap in cache_levels.values():ax.axvline(cap,c='grey',ls=':',lw=1)
axs[0,0].set_ylabel('GFLOP/s');axs[1,0].set_ylabel('Speedup vs scalar');axs[0,0].legend()
fig.tight_layout();fig.savefig('figures/locality.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(13,4))
def errors(ax,x,d,label):
    ax.errorbar(x,d.ns,yerr=[d.ns-d.low,d.high-d.ns],fmt='o-',capsize=3,label=label)
for v in ['scalar','native']:
    d=g.query('kernel=="multiply" and dtype=="float" and n==4194304 and shift==0 and build==@v').sort_values('stride')
    errors(axs[0],d.stride,d,v)
for sh in [0,1]:
    d=g.query('kernel=="multiply" and dtype=="float" and build=="native" and n in [64,67,65536,65539] and shift==@sh')
    errors(axs[1],range(len(d)),d,f'offset {sh*4} B')
axs[1].set_xticks(range(4),['64','67','65536','65539'])
for dt in ['float','double']:
    d=main.query('kernel=="multiply" and build=="native" and dtype==@dt')
    errors(axs[2],d.n,d,dt)
axs[2].set_xscale('log')
for ax,title in zip(axs,['Stride (elements)','Length (elements)','Length (elements)']):
    ax.set_xlabel(title);ax.set_ylabel('ns / element');ax.legend();ax.grid(alpha=.2)
fig.tight_layout();fig.savefig('figures/access.png',dpi=150)

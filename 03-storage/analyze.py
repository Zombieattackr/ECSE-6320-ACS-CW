from pathlib import Path
import os,json,numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
os.chdir(Path(__file__).resolve().parent)
rows=[];direction=[]
keys=['rw','bs_KiB','jobs','read_pct','span_MiB','direct']
for path in sorted(Path('raw').glob('*-*.json')):
    if path.name.startswith('setup'): continue
    rw,bs,jobs,pct,span,direct,trial=path.stem.split('-')
    j=json.loads(path.read_text())['jobs'][0]
    assert j['error']==0
    row=dict(zip(keys+[ 'trial'],[rw,*map(int,[bs,jobs,pct,span,direct,trial])]))
    ds=[j[d] for d in ('read','write') if j[d]['total_ios']]
    n=sum(x['total_ios'] for x in ds)
    assert all(x['short_ios']==0 and x['io_bytes']==x['total_ios']*int(bs)*1024 for x in ds)
    iops=sum(x['iops'] for x in ds)
    mean=sum(x['lat_ns']['mean']*x['total_ios'] for x in ds)/n/1000
    rows.append({**row,'ios':n,'iops':iops,'MiBs':sum(x['bw_bytes'] for x in ds)/2**20,'us':mean,'inflight':iops*mean/1e6,'actual_read_pct':100*j['read']['total_ios']/n,'depth1_pct':j['iodepth_level']['1']})
    for d in ['read','write']:
        if j[d]['total_ios']:
            lat=j[d]['lat_ns'];direction.append({**row,'direction':d,'ios':j[d]['total_ios'],**{'p'+str(p):lat['percentile'][f'{p:.6f}']/1000 for p in [50,95,99,99.9]}})
r=pd.DataFrame(rows); tails=pd.DataFrame(direction)
r.to_csv('processed/individual.csv',index=False);tails.to_csv('processed/directional_tails_us.csv',index=False)
g=r.groupby(keys).agg(iops=('iops','median'),lo_iops=('iops','min'),hi_iops=('iops','max'),us=('us','median'),lo_us=('us','min'),hi_us=('us','max'),MiBs=('MiBs','median'),lo_MiBs=('MiBs','min'),hi_MiBs=('MiBs','max'),inflight=('inflight','median'),actual_read_pct=('actual_read_pct','median'),trials=('trial','size')).reset_index()
assert (g.trials==3).all()
g.to_csv('processed/summary.csv',index=False)
span=g.span_MiB.max()
d=g.query('direct==1 and span_MiB==@span')
fig,ax=plt.subplots(2,2,figsize=(10,7))
def err(ax,x,y,d):
    ax.errorbar(d[x],d[y],yerr=[d[y]-d['lo_'+y],d['hi_'+y]-d[y]],fmt='o-',capsize=3,label=d.rw.iloc[0])
for rw in ['read','randread']:
    line=d.query('jobs==1 and rw==@rw').sort_values('bs_KiB')
    err(ax[0,0],'bs_KiB','MiBs',line);err(ax[0,1],'bs_KiB','us',line)
for rw,bs in [('randread',4),('read',128)]:
    q=d.query('rw==@rw and bs_KiB==@bs').sort_values('jobs')
    axis=ax[1,0 if bs==4 else 1]
    axis.errorbar(q.us,q.iops/1000,xerr=[q.us-q.lo_us,q.hi_us-q.us],yerr=[(q.iops-q.lo_iops)/1000,(q.hi_iops-q.iops)/1000],fmt='o-',capsize=3)
    for t in q.itertuples():axis.annotate(str(t.jobs),(t.us,t.iops/1000),xytext=(3,4),textcoords='offset points')
    axis.set(xlabel='Mean end-to-end latency (µs)',ylabel='Thousand IOPS',title=f'{bs} KiB {rw} · labels = workers')
for axis,yl in zip(ax[0],['MiB/s','Mean latency (µs)']):
    axis.set(xlabel='Block size (KiB)',ylabel=yl,title='One synchronous worker');axis.legend()
for axis in ax.flat:axis.grid(alpha=.2)
fig.tight_layout();fig.savefig('figures/storage.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(10,4))
mix=d.query('jobs==8 and bs_KiB==4').sort_values('read_pct')
err(ax[0],'read_pct','MiBs',mix);ax[0].set(xlabel='Target read share (%)',ylabel='MiB/s',title='Random 4 KiB · eight workers')
z=tails.query('rw=="randread" and bs_KiB==4 and span_MiB==@span and direct==1')
for col in ['p50','p95','p99','p99.9']:
    a=z.groupby('jobs')[col].agg(['median','min','max'])
    ax[1].errorbar(a.index,a['median'],yerr=[a['median']-a['min'],a['max']-a['median']],fmt='o-',capsize=2,label=col)
ax[1].set(xlabel='Synchronous workers',ylabel='Total I/O latency (µs, log scale)',yscale='log');ax[1].legend()
fig.tight_layout();fig.savefig('figures/tails_mix.png',dpi=150)

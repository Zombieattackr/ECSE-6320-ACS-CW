"""Offline data, coverage, report-link and plot checks. Run from any directory."""
import csv,json,re
from pathlib import Path
from collections import Counter
root=Path(__file__).resolve().parent
def read(p):
    with p.open() as f:return list(csv.DictReader(f))
for d in sorted(p for p in root.iterdir() if p.is_dir() and p.name[:2].isdigit()):
    s=read(d/'processed/summary.csv')
    assert s and all(int(row['trials'])==3 for row in s)
    for md in [d/'README.md',d/'REPORT.md']:
        for ref in re.findall(r'\]\(([^)]+)\)',md.read_text()):
            if '://' not in ref:assert (d/ref).is_file(),ref
    for png in (d/'figures').glob('*.png'):assert png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    if d.name.startswith('01'):
        r=read(d/'raw/trials.csv')
        assert {x['kernel'] for x in r}=={'multiply','axpy','stencil','copy_stream'}
        assert {x['build'] for x in r}=={'scalar','default','native'}
        assert len(r)==3*len(s) and all(float(x['sec'])>0 and int(x['tsc_ticks'])>0 for x in r)
    if d.name.startswith('02'):
        r=read(d/'raw/trials.csv')
        assert len(r)==3*len(s) and all(int(x['loads'])>0 for x in r)
        ctr=read(d/'raw/kernel_counters.csv')
        assert len(ctr)==15 and all(float(x['seconds'])>0 for x in ctr)
    if d.name.startswith('03'):
        r=read(d/'processed/individual.csv')
        raw=list((d/'raw').glob('*-*-*-*.json'))
        assert len(raw)==len(r)==3*len(s)
        for f in raw:
            j=json.loads(f.read_text())['jobs'][0]
            assert j['error']==0 and all(j[k]['short_ios']==0 for k in ['read','write'])
        assert set(int(x['bs_KiB']) for x in r)=={4,16,32,64,128,256}
    print(f'{d.name}: {len(s)} conditions, {len(r)} primary trials verified')

"""Use ONLY the automatically created regular file in the requested directory."""
import argparse, json, os, random, shutil, subprocess, tempfile
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--test-dir',type=Path,default=Path.cwd())
p.add_argument('--seconds',type=int,default=2)
p.add_argument('--mib',type=int,default=512)
p.add_argument('--extension',action='store_true',help='measure 64/128/256-worker random reads only, same total range')
p.add_argument('--fio',default='fio')
a=p.parse_args()
if a.extension and (a.mib<256 or a.mib%256): p.error('extended sweep requires a multiple of 256 MiB')
suffix='-extended' if a.extension else ''
dest=a.test_dir.resolve()
os.chdir(Path(__file__).resolve().parent)
assert a.seconds>=1 and a.mib>=128 and a.mib%32==0
assert shutil.disk_usage(dest).free>2*a.mib*2**20
raw=Path('raw');raw.mkdir(exist_ok=True)
subprocess.run(['bash','environment.sh'],stdout=(raw/('environment'+suffix+'.txt')).open('w'),check=True)
cpus=sorted(os.sched_getaffinity(0))
version=subprocess.check_output([a.fio,'--version'],text=True).strip()
if not version.startswith('fio-'): raise RuntimeError('Flexible I/O Tester required')
cases=set()
for bs in (4,16,32,64,128,256):
    for rw in ('randread','read'): cases.add((rw,bs,1,100,a.mib,1))
for rw,bs in [('randwrite',4),('write',128)]: cases.add((rw,bs,1,0,a.mib,1))
for jobs in (1,2,4,8,16,32):
    cases.add(('randread',4,jobs,100,a.mib,1))
    cases.add(('read',128,jobs,100,a.mib,1))
for rw,pct in [('randread',100),('randrw',70),('randrw',50),('randwrite',0)]:
    cases.add((rw,4,8,pct,a.mib,1))
cases.add(('randread',4,1,100,16,1))
cases.add(('randread',4,1,100,16,0))
if a.extension: cases={('randread',4,j,100,a.mib,1) for j in (64,128,256)}
with tempfile.TemporaryDirectory(prefix='fio-disposable-',dir=dest) as td:
    target=Path(td)/'payload'
    with target.open('xb') as f:
        for _ in range(a.mib): f.write(os.urandom(2**20))
        f.flush();os.fsync(f.fileno())
    cfg={'fio':version,'MiB':a.mib,'seconds':a.seconds,'cpu_pool':cpus,'filesystem':subprocess.check_output(['df','-T',str(target)],text=True),'safety':'new regular file, random initialized, fsync before trials'}
    (raw/('setup'+suffix+'.json')).write_text(json.dumps(cfg,indent=2))
    # Separate verified write/read, before any timed work.
    subprocess.run([a.fio,'--name=verify',f'--filename={target}','--size=4m','--bs=4k','--direct=1','--rw=write','--verify=crc32c','--do_verify=1','--verify_fatal=1','--allow_file_create=0'],check=True,stdout=(raw/('verify'+suffix+'.txt')).open('w'))
    for trial in range(3):
        order=sorted(cases);random.Random(774+trial).shuffle(order)
        for seq,(rw,bs,jobs,pct,span,direct) in enumerate(order):
            id=f'{rw}-{bs}-{jobs}-{pct}-{span}-{direct}-{trial}'
            out=raw/(id+'.json')
            # Global CLI options precede the job file. Set per-case overrides in the job itself.
            config=Path(td)/'case.fio'
            config.write_text(Path('job.fio').read_text()+f'filename={target}\nrw={rw}\nbs={bs}k\nnumjobs={jobs}\nrwmixread={pct}\nsize={span//jobs}m\noffset_increment={span//jobs}m\nruntime={a.seconds}\ndirect={direct}\ncpus_allowed={",".join(map(str,cpus))}\ncpus_allowed_policy=split\n')
            subprocess.run([a.fio,'--eta=never','--output-format=json','--output='+str(out),str(config)],check=True)
            j=json.loads(out.read_text())['jobs'][0]
            assert j['error']==0 and sum(j[d]['total_ios'] for d in ('read','write'))>0
            with (raw/('order'+suffix+'.csv')).open('w' if trial==seq==0 else 'a') as f:
                if trial==seq==0: f.write('trial,sequence,id\n')
                f.write(f'{trial},{seq},{id}\n')

#!/usr/bin/env bash
set -u
date -u
uname -a
cat /etc/os-release
head -26 /proc/cpuinfo
rg 'MemTotal|HugePages|Hugepagesize|AnonHugePages' /proc/meminfo
taskset -pc $$
gcc --version | head -1
python3 --version
python3 -c 'import matplotlib; print("matplotlib",matplotlib.__version__)'
df -hT .
for f in /sys/devices/system/cpu/smt/active /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor /sys/fs/cgroup/cpu.max /sys/kernel/mm/transparent_hugepage/enabled /proc/sys/kernel/perf_event_paranoid; do
  [ -r "$f" ] && echo "$f $(cat "$f")" || echo "$f unavailable"
done
command -v perf || echo "perf executable unavailable"
command -v fio || echo "fio executable unavailable"
lsblk -o NAME,SIZE,ROTA,MODEL,TRAN 2>&1 || true

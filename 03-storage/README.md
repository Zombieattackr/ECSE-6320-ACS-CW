# Storage performance under file I/O concurrency

Figures and CSVs are already generated. Each fio JSON corresponds to one measured run.

## Reproduce

Use Linux, Python 3, pandas, NumPy, matplotlib, and the Flexible I/O Tester. From this folder:

```bash
python3 -m pip install pandas numpy matplotlib
python3 run.py --test-dir /path/to/test-filesystem --seconds 2 --mib 512
python3 run.py --extension --test-dir /path/to/test-filesystem --seconds 2 --mib 512
python3 analyze.py
```

Supply an existing directory on the desired filesystem. The runner creates a private temporary directory and a new disposable regular file, fills it with random bytes, and removes it when finished. It has no device or existing-file target option. It needs at least twice the chosen test size free and generates real writes. For longer measurements, use a **fresh copy** of the project and increase seconds and range. The range must be a multiple of 32 MiB. Keep one configuration per raw directory. The native measurements used fio 3.41. For an optional fio 3.39 source build, run `bash build.sh` and add `--fio ./build/src/fio` to the run command. Build dependencies include make, gcc, libc headers and curl.

The runner expands job.fio into one temporary job file per case. Raw JSON preserves the actual options. raw/order.csv records randomized order, setup.json records range, version, CPU pool and filesystem. The disposable filename in fio metadata is historical. All jobs have depth one, each worker accesses a disjoint slice, and total range stays fixed. Each trial records fio total latency, inclusive of submission. Mixed-direction percentiles stay separate to avoid averaging nonadditive quantiles. processed/summary.csv uses medians of three independent trials with observed ranges. Plot error bars show those ranges. Byte rates use powers of two.

## AI-use note

OpenAI Codex (GPT-6 Astra Medium) helped write the code and scripts, and gave my resulting data and analysis a sanity check.

# Cache and memory performance profiling

The standalone Linux/x86-64 benchmark uses GCC, pthreads, CPUID and Linux perf_event_open. It needs about 1.2 GiB free RAM at peak. Run in a fresh project copy with multiple allowed CPUs.

```bash
python3 -m pip install pandas numpy matplotlib
python3 run.py
python3 analyze.py
```

run.py builds bench.c, captures environment and CPUID, chooses workers within the allowed mask, checks every exit status and randomizes three repetitions. build.sh compiles with -O3 -march=native. The analyzer expects at least two available CPUs so it can produce the load plots. The native run exposed 16 logical CPUs and used up to eight load workers plus one probe. raw/trials.csv contains unaggregated elapsed time, completed dependent loads, completed worker operations, memory page backing, hardware event status and a checksum. processed/individual.csv and summary.csv preserve units and observed trial ranges. The four-byte ring offset and eight-byte streaming payload report useful bytes. Index-array traffic, write allocate, writeback and line overfetch are excluded. To rerun only the plots, use analyze.py. The PMU results in the report come from counter\_run.py. If permission prevents event collection, rerun counter_run.py with appropriate local privileges and regenerate the analysis.

## AI-use note

OpenAI Codex (GPT-6 Astra Medium) helped write the code and scripts, and gave my resulting data and analysis a sanity check.

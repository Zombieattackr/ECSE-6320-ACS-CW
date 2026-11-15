# SIMD advantage profiling

To reproduce on x86-64 Linux with GCC and GNU objdump:

```bash
python3 -m pip install numpy pandas matplotlib
OPENBLAS_NUM_THREADS=1 python3 run.py
python3 analyze.py
```

The largest three-array double case needs roughly 1.2 GiB free memory plus runtime overhead. The runner pins itself to the first allowed logical CPU, builds six shared objects, validates each case and gives raw/trials.csv and raw/instructions.txt. GCC's detailed vectorizer logs remain in build/ after reproduction. build.sh records all compiler flags. The native build adapts to the local ISA. This experiment uses the x86 timestamp counter. Other ISAs require a different timer/build. Figures are generated from the trial CSV. processed/individual.csv records throughput, elapsed time, useful bandwidth and reference ticks per element. processed/summary.csv groups the three repetitions. Use a fresh copy to avoid overwriting the supplied measurements.

## AI-use note

OpenAI Codex (GPT-6 Astra Medium) helped write the code and scripts, and gave my resulting data and analysis a sanity check.

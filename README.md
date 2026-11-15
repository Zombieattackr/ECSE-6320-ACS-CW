# Three architecture profiling labs

Each numbered folder is self-contained and includes its prediction, source, build and run commands, raw evidence, processed CSVs, plotting script, figures, AI-use note and a short report. I collected the included measurements on an Aorus 15P laptop with Intel Core i7-11800H and 32GB DDR4 running Ubuntu 26.04.1 LTS. Storage tests used an ext4 file on a Corsair MP400 NVMe SSD.

SIMD advantage: [Report](01-simd/REPORT.md) , [Reproduce](01-simd/README.md) , Measured three kernels, three code-generation targets, six working-set sizes, two precisions, tail/alignment and stride
Cache and memory: [Report](02-memory/REPORT.md) , [Reproduce](02-memory/README.md) , Measured dependent load latency, independent chains, cache footprint, worker throughput, page locality and loaded latency
Storage: [Report](03-storage/REPORT.md) , [Reproduce](03-storage/README.md) , Measured fio direct file I/O, random and sequential blocks, read/write mix, concurrency and tail latency

## Review and reproduction

The README in each folder gives the commands to rebuild and regenerate data. Run the projects one at a time. Use a separate copy when rerunning so the originally collected data remain available for comparison. 

The environment scripts use ripgrep (rg) for a short memory-information extract. All experiment drivers require Python 3. The two CPU projects target Linux x86-64 with GCC. Python plotting uses numpy, pandas and matplotlib. Storage additionally requires the Flexible I/O Tester. For aggregate verification run `python3 verify.py` from this directory.

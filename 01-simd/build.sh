#!/usr/bin/env bash
set -eu
mkdir -p build raw
gcc -O2 -shared -fPIC timer.c -o build/timer.so
for variant in scalar default native; do
 case $variant in
 scalar) flags="-march=x86-64 -fno-tree-vectorize";;
 default) flags="-march=x86-64";;
 native) flags="-march=native -mprefer-vector-width=512";;
 esac
 for dtype in float double; do
 base=${variant}_${dtype}
 gcc -O3 -shared -fPIC -ffp-contract=off -fno-tree-loop-distribute-patterns $flags -DREAL=$dtype -fopt-info-vec-optimized=build/$base.log kernels.c -o build/$base.so
 for k in multiply axpy stencil; do
   echo "$base $k"
   objdump -d -M intel --disassemble=$k build/$base.so | awk '/(mul|add)(ps|pd|ss|sd)/ && ++n<=4'
 done
 done
done >raw/instructions.txt

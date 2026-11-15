#!/usr/bin/env bash
set -eu
mkdir -p build
gcc -O3 -march=native -std=gnu11 -Wall -Wextra -pthread bench.c -o build/bench

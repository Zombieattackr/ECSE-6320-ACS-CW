#!/usr/bin/env bash
# Optional source build. The typical Linux alternative is to install the fio package.
set -eu
mkdir -p build
cd build
curl -fLsS https://deb.debian.org/debian/pool/main/f/fio/fio_3.39.orig.tar.gz -o fio.tar.gz
echo '501237032d617fb5dd3752974242e8c741fe345f4efa2492d52ccd5ddf945d7b  fio.tar.gz' | sha256sum -c -
mkdir -p src
tar xf fio.tar.gz -C src --strip-components=1
cd src
./configure
make -j4
./fio --version

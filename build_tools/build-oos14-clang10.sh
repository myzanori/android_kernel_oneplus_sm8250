#!/usr/bin/env bash
set -eu
ROOT=/home/myzanori/Desktop/projects/Oneplus_9R/kernel
cd "$ROOT/oos14"
export PATH="$ROOT/clang-10/bin:$ROOT/toolchains/bin:$PATH"
export LD_LIBRARY_PATH="$ROOT/clang-10/lib:$ROOT/toolchains/libcompat:${LD_LIBRARY_PATH:-}"
export KCFLAGS="-Wno-strict-prototypes -Wno-missing-prototypes -Wno-unused-function -Wno-unused-variable"

# Export OPLUS feature make-variables so Kbuild objs behind `ifeq (...)` get selected
python3 - > "$ROOT/.oplus_env_a14.sh" <<'PY'
import re
for line in open("oplus_native_features.mk"):
    m = re.match(r'^(OPLUS_[A-Z0-9_]+)=(.*)$', line.rstrip("\n"))
    if m:
        k, v = m.group(1), m.group(2)
        print("export %s='%s'" % (k, v.replace("'", "'\\''")))
PY
. "$ROOT/.oplus_env_a14.sh"

CL="$ROOT/clang-10/bin/clang"
MK=(O=out ARCH=arm64 CC="$CL" CLANG_TRIPLE=aarch64-linux-gnu- BRAND_SHOW_FLAG=oneplus
    LD="$ROOT/toolchains/gcc-64/bin/aarch64-linux-android-ld" HOSTCC="$CL" HOSTCXX="$ROOT/clang-10/bin/clang++"
    CROSS_COMPILE=aarch64-linux-gnu-
    CROSS_COMPILE_ARM32=arm-linux-gnueabi-)
echo ">>> olddefconfig A14"
make "${MK[@]}" olddefconfig
echo ">>> build A14 (clang10, Image)"
make -j"$(nproc)" "${MK[@]}" Image
ls -la out/arch/arm64/boot/Image

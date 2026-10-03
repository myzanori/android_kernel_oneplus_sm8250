# OnePlus 9R — OxygenOS 14 Custom Kernel (ReSukiSU + SUSFS)

Custom `4.19.157` kernel for the **OnePlus 9R (lemonades / SM8250‑AC)** running
**stock OxygenOS 14 (Android 14)**, built from the official OnePlus OSS source.

Root via **ReSukiSU** + kernel‑level hiding via **SUSFS v2.3.0**, with full
camera / fingerprint / vendor‑module compatibility.

---

## Device / target

| | |
|---|---|
| Device | OnePlus 9R (LE2101), SM8250‑AC, project `20828` |
| ROM | OxygenOS 14 — `LE2101_14.0.0.2401(EX01)`, Android 14 (SDK 34) |
| Kernel base | Linux `4.19.157` |
| Boot | Android boot image **header v2** (kernel + ramdisk + DTB) |
| Slots | A/B (`boot_a`, `boot_b`) |

---

## Branches

| Branch | What it is |
|---|---|
| `main` | **Pristine stock OOS 14 source** — untouched copy of OnePlusOSS `oneplus/sm8250_u_14.0.0_op9r` (`Synchronize code for OnePlus LE2101_14.0.0.2401(EX01)`). Use this to diff. |
| `oos14-resukisu-susfs` | **Working custom kernel** — ReSukiSU + SUSFS v2.3.0 + the OPLUS/vendor integration and build fixes below. |
| `oos13-resukisu-susfs` *(legacy)* | Earlier OOS 13.1 attempt (`sm8250_t_13.1_op9r`). Kept for history only — **not** for Android 14. |

> Rule of thumb: `main` = stock, every other branch = a working configuration.

---

## What is integrated

### 1. Root & hiding
- **ReSukiSU** — `4.2.0-rc3`, non‑GKI, **inline hooks** (`susfs_inline_hook_patches.sh`).
- **SUSFS v2.3.0** — kernel‑side hiding, enabled:
  - `CONFIG_KSU_SUSFS_SUS_PATH`
  - `CONFIG_KSU_SUSFS_SUS_MOUNT`
  - `CONFIG_KSU_SUSFS_SUS_KSTAT`
  - `CONFIG_KSU_SUSFS_SUS_MAP`
  - `CONFIG_KSU_SUSFS_OPEN_REDIRECT`
  - `CONFIG_KSU_SUSFS_SPOOF_UNAME`
  - `CONFIG_KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG`
  - `CONFIG_KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS`
- `CONFIG_KALLSYMS_ALL=y`, `CONFIG_SECCOMP(_FILTER)=y`.

### 2. OPLUS vendor integration
The official kernel tree ships **without** OPLUS vendor code (it's in a *separate*
repo). Both are required to build **and** to keep the stock camera/vendor stack working:

- Repo: `OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8250`
- Branch: `oneplus/sm8250_u_14.0.0_op9r` (**must match the ROM build**)
- Added into the tree:
  - `vendor/oplus/**` (charger, power, sched_assist, touchpanel, fingerprint BSP, …)
  - `vendor/qcom/**` (incl. `camera-devicetree`)
  - `techpack/{camera,display,video}` (the kernel tree only ships `techpack/stub`)

### 3. Config parity with stock
Built on the **stock config extracted from the device** (`/proc/config.gz` via
`extract-ikconfig`), so userspace/vendor interfaces match:

- F2FS for Android 14: `CONFIG_F2FS_FS_COMPRESSION`, `LZ4`, `ZSTD`, `DEDUP`,
  `CONFIG_F2FS_APPBOOST`, `CONFIG_LZ4HC_COMPRESS`
- `CONFIG_OPLUS_FEATURE_SCHED_ASSIST`, `CONFIG_OPLUS_LOCKING_STRATEGY`
- `MODULE_SIG_FORCE` **off** → the 35 OnePlus‑signed vendor `.ko` modules load
- Extra: `LOCALVERSION=-oos…-ksu-susfs`

---

## Toolchain (matches the stock kernel)

The stock OOS kernel was built with **clang 10.0.7 + GNU ld 2.27**; using the same
generation avoids the OPLUS hand‑written asm issues newer clang hits.

| | |
|---|---|
| Compiler | clang 10 (ZyC/AOSP-style LLVM 10.0.x) |
| Linker | **GNU ld (binutils‑2.27)** — `aarch64-linux-android-ld` |
| CROSS_COMPILE | `aarch64-linux-gnu-` |
| `CONFIG_LD_IS_LLD` | **not set** (we use GNU ld) |

---

## Build from source

### 1. Get both sources (same branch!)
```bash
git clone -b oneplus/sm8250_u_14.0.0_op9r --depth=1 \
  https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250.git oos14

git clone -b oneplus/sm8250_u_14.0.0_op9r --depth=1 \
  https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8250.git oos14-modules
```

### 2. Assemble the tree
```bash
cd oos14
# vendor + qcom
cp -a ../oos14-modules/vendor .
# camera/display/video techpacks
cp -an ../oos14-modules/kernel/msm-4.19/. .
```
The OPLUS code references `vendor/...` via symlinks; resolve them to real paths, e.g.:
```bash
find . -type l | while read l; do
  t=$(readlink "$l"); case "$t" in *vendor/*)
    sub=$(printf '%s' "$t" | sed -E 's#^.*(vendor/)#\1#')
    src="../oos14-modules/$sub"
    [ -e "$src" ] && { rm -f "$l"; cp -a "$src" "$l"; }
  ;; esac
done
```

### 3. Apply root + hiding
- Add `KernelSU/` (ReSukiSU) and `fs/susfs.c` + `include/linux/susfs*.h`, and apply
  `susfs_inline_hook_patches.sh`.
- **Critical:** export the OPLUS feature make‑variables, or the link fails with
  `undefined symbol: ufsf_*` / `is_reclaim_should_cancel` / `update_user_tasklist`:
```bash
python3 - > .oplus_env.sh <<'PY'
import re
for line in open("oplus_native_features.mk"):
    m = re.match(r'^(OPLUS_[A-Z0-9_]+)=(.*)$', line.rstrip("\n"))
    if m: print("export %s='%s'" % (m.group(1), m.group(2).replace("'", "'\\''")))
PY
```

### 4. Build
```bash
export PATH="$PWD/../clang-10/bin:$PATH"
export LD_LIBRARY_PATH="$PWD/../clang-10/lib:$PWD/../toolchains/libcompat"
export KCFLAGS="-Wno-strict-prototypes -Wno-missing-prototypes -Wno-unused-function"
. .oplus_env.sh

make O=out ARCH=arm64 \
  CC=clang CLANG_TRIPLE=aarch64-linux-gnu- \
  HOSTCC=clang HOSTCXX=clang++ \
  LD=aarch64-linux-android-ld \
  CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-gnueabi- \
  BRAND_SHOW_FLAG=oneplus \
  vendor/kona-perf_defconfig

./scripts/config --file out/.config --set-str LOCALVERSION "-oos14-ksu-susfs"
./scripts/config --file out/.config --disable MODULE_SIG_FORCE
yes "" | make O=out ARCH=arm64 olddefconfig

make O=out ARCH=arm64 ... -j"$(nproc)" Image
# -> out/arch/arm64/boot/Image  (~45 MB)
```

### 5. Repack
Swap **only** the `Image` into the stock boot image (keep the stock ramdisk + DTB):
```bash
python3 scripts/repack-boot.py stock_boot.img \
  out/arch/arm64/boot/Image boot-oos14-ksu-susfs.img
```

---

## Flash

**AnyKernel3 (recovery / KernelSU manager)**
`OnePlus_9R_OOS14_Kernel_4.19.157_ReSukiSU_SUSFS_v2.3.0_AnyKernel3.zip`

**Fastboot (both slots)**
```bash
fastboot flash boot_a boot-oos14-ksu-susfs.img
fastboot flash boot_b boot-oos14-ksu-susfs.img
```

**Safe test first (RAM only, no flash):**
```bash
fastboot boot boot-oos14-ksu-susfs.img
```

---

## Verify after boot

```bash
adb shell cat /proc/version                     # 4.19.157-perf+ ... <your build>
adb shell sys.boot_completed                    # 1
adb shell su -c id                              # uid=0(root)  context=u:r:ksu:s0
adb shell "dumpsys media.camera | grep -i 'Number of camera'"   # 8
adb shell "dumpsys fingerprint | head -3"        # prints enrolled
adb shell lsmod | wc -l                          # ~35 vendor modules
adb shell "mount | grep ' /data '"               # f2fs ... inlinecrypt
```

---

## Known behaviour / notes

- **`khungtaskd` "hung task" warnings** at boot are OPLUS's own parked `UID_PERF`
  kthreads (`drivers/misc/uid_sys_stats.c`) + OPLUS's 60 s timeout
  (`CONFIG_OPLUS_FEATURE_HUNG_TASK_ENHANCE`). Present in stock too — benign.
- **SELinux `avc: denied { find }` for `vendor.oplus.*` services** — vendor sepolicy
  noise, not kernel.
- **OTA / build matching:** the kernel is tied to the ROM. If OnePlus bumps the
  kernel base, rebuild from the matching `oneplus/sm8250_u_14.0.0_*` commit.
  `ro.build.display.id` staying on the same build means the OTA didn't touch the kernel.
- **Camera** requires the matching `techpack/camera` + camera DTB from the modules
  repo — that's why version matching matters.

---

## Credits

- [OnePlusOSS](https://github.com/OnePlusOSS) — official kernel + modules source
- [ReSukiSU](https://github.com/ReSukiSU/ReSukiSU) — KernelSU fork
- [SUSFS](https://gitlab.com/simonpunk/susfs4ksu) — path/mount hiding
- KernelSU / KernelSU‑Next contributors

## Disclaimer

Kernel flashing is risky. Provided **as is**, no warranty. Keep a full backup
(`boot`, `dtbo`, `recovery`, `vbmeta` for both slots) and know your restore path.

# Mystic Kernel — Maintenance & Update SOP (Standard Operating Procedure)

This guide documents the exact workflow to update **ReSukiSU** (KernelSU fork) and **SUSFS** (Kernel-side SU hiding) for Mystic Kernel on OnePlus 9R (SM8250 / OxygenOS 14).

---

## 1. Architecture Wiring

| Component | Path / Location | Purpose |
| :--- | :--- | :--- |
| **ReSukiSU Core** | `KernelSU/` (symlinked via `drivers/kernelsu -> ../KernelSU/kernel`) | KernelSU driver and managers |
| **SUSFS Source** | `fs/susfs.c`<br>`include/linux/susfs.h`<br>`include/linux/susfs_def.h` | Kernel-side hiding layer |
| **Inline Hook Script** | `susfs_inline_hook_patches.sh` | Patches syscalls & VFS hooks (`fs/exec.c`, `fs/open.c`, `fs/stat.c`, `kernel/sys.c`, etc.) |
| **Defconfig** | `arch/arm64/configs/vendor/kona-perf_defconfig` | Hardcoded config baseline |
| **Version Truth** | `mystic_version.sh` | Micro-versioning (`v1.0.xx`) |

---

## 2. The Safe Update Workflow

> [!IMPORTANT]
> Both KernelSU and SUSFS modify the same core kernel files using inline hooks. The hook script safely skips files already containing hooks. Therefore, **you must reset the hooked files to stock pristine before re-applying updated hooks**.

### Step 0: Create a Backup Checkpoint
```bash
cd ~/Desktop/projects/Oneplus_9R/kernel/oos14
git add -A && git commit -m "checkpoint: pre-update backup" || true
git branch backup-$(date +%Y%m%d)
```

### Step 1: Update ReSukiSU Driver
```bash
git -C KernelSU fetch --tags origin
git -C KernelSU checkout <NEW_TAG>   # e.g., v4.2.1
```

### Step 2: Update SUSFS Source Files
Replace the following files with the matching release from SUSFS:
- `fs/susfs.c`
- `include/linux/susfs.h`
- `include/linux/susfs_def.h`
- `susfs_inline_hook_patches.sh` (must match the SUSFS `PATCH_LEVEL`)

### Step 3: Reset Hooked Files to Pristine State
```bash
git checkout stock-pristine -- \
  fs/exec.c fs/open.c fs/read_write.c fs/stat.c fs/namei.c \
  drivers/input/input.c security/security.c \
  security/selinux/hooks.c security/selinux/ss/services.c \
  kernel/reboot.c kernel/sys.c
```

### Step 4: Re-apply Inline Hooks
```bash
bash susfs_inline_hook_patches.sh
```

### Step 5: Bump Version
Edit `mystic_version.sh`:
```bash
export MYSTIC_VERSION="1.0.02"  # increment by .01
```

### Step 6: Compile & Test in RAM
```bash
../build-oos14-clang10.sh

# Test in RAM first — never flash blind!
adb reboot bootloader
fastboot boot ../Mystic_Releases/Mystic_9R_myzanori_OOS14_v1.0.02.img
```

---

## 3. Post-Boot Verification Checklist

Once the test kernel boots into RAM:

```bash
# 1. Check kernel banner & uname
adb shell cat /proc/version
adb shell uname -r

# 2. Check SUSFS version & active features
adb shell "su -c '/data/adb/ksu/bin/ksu_susfs show version'"
adb shell "su -c '/data/adb/ksu/bin/ksu_susfs show enabled_features'"

# 3. Check vendor module loading (Must be 35/35 loaded)
adb shell "lsmod | wc -l"

# 4. Check camera subsystem (Must show 8 sensors)
adb shell "dumpsys media.camera | grep -i 'Number of camera'"

# 5. Check network optimizations
adb shell cat /proc/sys/net/ipv4/tcp_congestion_control   # should be 'bbr'
adb shell cat /proc/sys/net/core/default_qdisc           # should be 'fq_codel'
```

---

## 4. Permanent Flashing
Only flash after all 5 verification points pass:

```bash
adb reboot bootloader
fastboot flash boot_a ../Mystic_Releases/Mystic_9R_myzanori_OOS14_v1.0.02.img
fastboot flash boot_b ../Mystic_Releases/Mystic_9R_myzanori_OOS14_v1.0.02.img
fastboot reboot
```

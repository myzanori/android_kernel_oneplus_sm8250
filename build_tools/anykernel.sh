### AnyKernel3 Configuration for Mystic Kernel (SM8250 / Kona Unified)
# properties
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=0
device.name1=lemonades
device.name2=lemonadep
device.name3=kebab
device.name4=kebabt
device.name5=instantnoodle
device.name6=instantnoodlep
device.name7=OnePlus9R
device.name8=OnePlus8T
device.name9=OnePlus8
device.name10=OnePlus8Pro
device.name11=LE2101
device.name12=KB2001
device.name13=KB2000
device.name14=KB2003
device.name15=KB2005
device.name16=KB2007
device.name17=IN2011
device.name18=IN2021
supported.versions=11-14
supported.patchlevels=

# shell variables
block=boot;
is_slot_device=1;
ramdisk_compression=auto;
patch_vbmeta_flag=auto;

## AnyKernel methods (DO NOT CHANGE)
# import patching functions/variables - see for reference
. tools/ak3-core.sh;

## AnyKernel boot install
dump_boot;

# write new kernel Image while keeping stock DTB & ramdisk
write_boot;
## end boot install

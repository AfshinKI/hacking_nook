#!/usr/bin/env bash
# Write a Nook rooting image to an SD card, with guards.
#
#   ./tools/flash-sd.sh <image.img|.img.gz> /dev/sdX
#
# Handles both kinds of file people call an ".img":
#   * a whole-disk image (has an MBR partition table)  -> written to the disk
#   * a bare filesystem image (no partition table)     -> an MBR is created and
#     the filesystem is written into partition 1
# The second case matters: NookManager1.2.2.img is a bare FAT32 filesystem, and
# its boot ramdisk mounts /dev/block/mmcblk1p1. Written straight to the disk it
# boots as far as "loading..." and then hangs forever, because that partition
# does not exist. See docs/02-rooting.md.
#
# Put the card in a USB card reader — NOT in the Nook. Through the Nook you only
# see a mounted partition, and the device is using it.
#
# The guards exist because the failure mode of a typo here is "overwrite the
# laptop's system disk".
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }

# `set -e` plus `pipefail` can kill this script with no output at all — a
# SIGPIPE in a pipeline is enough. Always say where we died.
trap 'echo "ERROR: aborted at line $LINENO (exit $?)" >&2' ERR

[ $# -eq 2 ] || die "usage: $0 <image.img|.img.gz> /dev/sdX"
IMAGE="$1"
DEV="$2"

[ -f "$IMAGE" ] || die "no such image: $IMAGE"
[ -b "$DEV" ]   || die "not a block device: $DEV"

# --- guard 1: must be a whole disk, not a partition ------------------------
case "$DEV" in
    *[0-9]) die "$DEV looks like a partition. Pass the whole disk, e.g. /dev/sdb" ;;
esac

NAME=$(basename "$DEV")

# --- guard 2: must be removable -------------------------------------------
REMOVABLE=$(cat "/sys/block/$NAME/removable" 2>/dev/null || echo 0)
[ "$REMOVABLE" = "1" ] || die "$DEV is not marked removable. Refusing."

# --- guard 3: must be USB -------------------------------------------------
TRAN=$(lsblk -dno TRAN "$DEV")
[ "$TRAN" = "usb" ] || die "$DEV is on the '$TRAN' bus, not usb. Refusing."

# --- guard 4: must be small ------------------------------------------------
# lsblk, not `blockdev --getsize64`: blockdev opens the device and so needs root,
# and we want every guard to run *before* we ask for any privilege.
BYTES=$(lsblk -bdno SIZE "$DEV")
GIB=$(( BYTES / 1024 / 1024 / 1024 ))
[ "$GIB" -le 64 ] || die "$DEV is ${GIB} GiB. Too big to be a Nook SD card. Refusing."

# --- guard 5: must not hold a mounted filesystem we care about -------------
while read -r mp; do
    case "$mp" in
        /|/boot|/boot/efi|/home|/usr|/var)
            die "$DEV is mounted at $mp. Refusing." ;;
    esac
done < <(lsblk -no MOUNTPOINT "$DEV")

echo "About to COMPLETELY OVERWRITE this device:"
echo
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINT,TRAN,MODEL "$DEV"
echo
echo "  image:  $IMAGE  ($(du -h "$IMAGE" | cut -f1))"
echo "  target: $DEV  (${GIB} GiB, removable, usb)"
echo
read -r -p "Type the device name again to confirm ($DEV): " CONFIRM
[ "$CONFIRM" = "$DEV" ] || die "confirmation did not match. Nothing written."

# An unpartitioned card is mounted as the disk itself, so iterate over the disk
# *and* its partitions. Missing this leaves the target mounted while we write.
echo "==> unmounting anything on $DEV"
for node in $(lsblk -lno PATH "$DEV"); do
    if findmnt -rn -S "$node" >/dev/null 2>&1; then
        sudo umount "$node" && echo "    unmounted $node"
    fi
done

# --- does the image carry its own partition table? -------------------------
# Read the four MBR entries at offset 446. All-zero means it is a bare
# filesystem image and needs to go *inside* a partition, not over the disk.
#
# Done in Python rather than `... | head -c 512`: head exits early, the producer
# takes SIGPIPE, and under `pipefail` + `set -e` the script dies silently.
reader() { case "$IMAGE" in *.gz) gzip -dc "$IMAGE" ;; *) cat "$IMAGE" ;; esac; }

read -r HAS_PTABLE IMAGE_SECTORS < <(python3 - "$IMAGE" <<'PYEOF'
import gzip, os, sys
path = sys.argv[1]
opener = gzip.open if path.endswith(".gz") else open
with opener(path, "rb") as fh:
    head = fh.read(512)
    if path.endswith(".gz"):
        size = len(head)
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            size += len(chunk)
    else:
        size = os.path.getsize(path)
has = any(head[446 + i * 16 + 4] for i in range(4))
print("yes" if has else "no", size // 512)
PYEOF
)

# partition 1 node: /dev/sdb -> /dev/sdb1, /dev/mmcblk0 -> /dev/mmcblk0p1
case "$NAME" in
    mmcblk*|nvme*|loop*) PART="${DEV}p1" ;;
    *)                   PART="${DEV}1"  ;;
esac

if [ "$HAS_PTABLE" = "yes" ]; then
    echo "==> image has its own partition table; writing to the whole disk"
    reader | sudo dd of="$DEV" bs=4M status=progress conv=fsync
else
    echo "==> image is a bare filesystem (no partition table)"
    echo "    creating an MBR and writing it into partition 1"
    # Start at sector 63: the convention these 2011-era tools were built around,
    # and NookManager'"'"'s own format_unused_sdcard adds p2 after p1 later.
    printf "63,%s,c,*\n" "$IMAGE_SECTORS" | sudo sfdisk --no-reread --wipe always "$DEV"
    sudo partprobe "$DEV" 2>/dev/null || true
    sleep 2
    [ -b "$PART" ] || die "expected $PART to exist after partitioning"
    reader | sudo dd of="$PART" bs=4M status=progress conv=fsync
fi

sync
sudo blockdev --rereadpt "$DEV" 2>/dev/null || true
echo
echo "==> done. New layout:"
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL "$DEV"
echo
echo "Now: eject the card, put it in the Nook while the Nook is POWERED OFF,"
echo "then power on. It boots from SD."

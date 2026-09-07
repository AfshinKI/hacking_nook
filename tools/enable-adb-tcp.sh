#!/usr/bin/env bash
# Make the Nook listen for adb over Wi-Fi at every boot.
#
#   ./tools/enable-adb-tcp.sh          # enable, then reboot the device
#   ./tools/enable-adb-tcp.sh --off    # back to USB only
#
# `adb tcpip 5555` does the same thing but does not survive a reboot: it sets
# service.adb.tcp.port on the running system only. Android reads
# /data/local.prop before starting services, and /data persists, so writing the
# property there makes it stick.
#
# Editing /init.rc would be the obvious alternative and does not work: / is a
# read-only ramdisk unpacked from uRamdisk at every boot, so changes are lost.
#
# SECURITY: adb on Android 2.1 predates RSA authentication (added in 4.2.2), and
# this device's adbd runs as root. Anyone on the same network gets an
# unauthenticated root shell on the Nook. Fine on a home LAN you control; not
# something to leave on elsewhere.
set -euo pipefail

PORT="${PORT:-5555}"
PROP=/data/local.prop

adb get-state >/dev/null 2>&1 || { echo "no device over adb; plug in USB" >&2; exit 1; }

TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

if [ "${1:-}" = "--off" ]; then
    echo "==> removing the property"
    adb shell "rm -f $PROP"
else
    # Preserve any other properties already set there.
    adb shell "cat $PROP 2>/dev/null" | tr -d '\r' | grep -v '^service\.adb\.tcp\.port=' > "$TMP" || true
    echo "service.adb.tcp.port=$PORT" >> "$TMP"
    adb push "$TMP" "$PROP" >/dev/null
    # adbd runs as root here, so the pushed file is already root-owned;
    # toolbox chown rejects numeric ids, so use busybox when fixing perms.
    adb shell "/system/xbin/busybox chmod 644 $PROP" >/dev/null 2>&1 \
        || adb shell "chmod 644 $PROP" >/dev/null 2>&1 || true
    echo "==> $PROP now:"
    adb shell "cat $PROP" | tr -d '\r' | sed 's/^/    /'
fi

echo "==> rebooting so init re-reads it"
adb reboot
echo "    then:  adb connect <nook-ip>:$PORT"

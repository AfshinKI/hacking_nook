# 08 — Innovetron boot, sleep and power-off artwork

The BNRV300 firmware 1.2.2 has separate artwork for different startup stages.
Changing only the screensaver does not replace its boot or power-off branding.

See [the artwork directory](../assets/innovetron/README.md) for the generated
sources, exact prompts, device files, destination mapping and rollback notes.

## What we found on the device

- Early boot: `booting.pgm` at the root of VFAT partition `/dev/block/mmcblk0p1`.
  The original is binary P5, 800×600, max value 255, with the portrait artwork
  rotated clockwise. Preserve that encoding and orientation.
- Android loading logo: `/system/assets/boot_images/render-0.png`, 512×256 RGBA.
  `render-1.png` through `render-5.png` are 256×32 progress frames. The strings
  in `/system/bin/bootanimation` reference those six paths explicitly.
- Normal shutdown: `/system/assets/shutdown_images/cold_boot_screen.png`.
  Despite its name, it says the Nook has turned off. Auto-shutdown has its own
  `autoshutdown_screen.png`. Both are 600×800 RGB.
- Sleep/lock: `screensaver_dir` and `screensaver_current_file` in the settings
  provider identify the chosen picture. This device used a single JPEG in
  `/media/screensavers/Extra/`. A fallback is
  `/system/media/screensaver/default.png`.
- Preserve low-battery, charging and factory/recovery images, which communicate
  device conditions rather than ordinary branding.

The seconds spent booting remain. NookPanel's window flags dismiss the slide
lock when the app starts; the custom pictures cover the stages before that.

## Backups and installation

Original image files, the settings DB, framework resource APK and the exact
installation script are in the gitignored `backups/branding-2026-09-12/`.
Full-disk backup attempts were stopped because of slow Wi-Fi transfer; files
ending `.partial` are incomplete and **must not be used as recovery images**.
The completed individual image backups are the rollback source for this change.

The installation staged files under `/data/local/tmp/innovetron-artwork`,
compared MD5 checksums against the host, temporarily remounted `/system` and the
boot VFAT partition read-write, copied each image to a sibling temporary file,
compared its contents, then renamed it into place. It restored `/system` to
read-only and unmounted the boot partition. No firmware image was flashed.

The Nook's toolbox commands do not support many familiar options. Use
`/system/xbin/busybox` for mkdir, cp, cmp, mv, chmod and chown. Its symlink list
overstates its compiled applets: `gzip` and `nc` are absent. `/system/bin/gzip`
works as a stdin/stdout filter but does not accept the usual `-c` flag.

This ADB daemon does not support `exec-out`. For a binary stream, first set
`/system/xbin/busybox stty raw -echo` within the same remote shell. A streamed
booting.pgm and a compressed/decompressed copy were byte-compared successfully
against `adb pull` before attempting the optional full-disk backup.

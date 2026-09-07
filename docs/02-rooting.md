# 02 — Rooting the NST (the 2026 way)

> **Nothing here has been executed yet.** This is the plan; record what actually
> happened in [99-lab-log.md](99-lab-log.md) as we go.

## Where we actually are (2026-09-06)

The device is connected and enumerating: `lsusb` shows
`ID 2080:0003 Barnes & Noble NOOK Simple Touch`, exposing two volumes:

| Device | Size | Label | What it is |
|---|---|---|---|
| `/dev/sdc` | 240 MB | `NOOK` | The internal user-accessible partition. Holds `My Files`, `screensavers`, `.devicesalt`, and Adobe DE activation |
| `/dev/sdd` | 1.8 GB | `NOOGIE` | The 2 GB microSD card sitting in the Nook |

The card's label is `NOOGIE` — the name of the classic NST rooting image — but
its contents are **empty** apart from `System Volume Information`. So the card
was used with noogie at some point and later reformatted. It is free to reuse.

Both volumes are copied to `backups/2026-09-06/` (gitignored). That covers the
user data, **not** the system image — a full internal image still needs either
noogie or a rooted adb shell, so it happens as part of the rooting run itself.

The device boots normally into Android, so it is **not currently rooted** in any
way that changes USB behaviour.

## Before anything: identify and back up

1. **Which model?** Settings → Device Info. `BNRV300` = plain NST,
   `BNRV350` = NST with GlowLight. The GlowLight needs GlowLight-aware images.
2. **Which firmware?** Same screen. `1.2.2` is the last and the one the modern
   tooling targets. `1.1.5` also has a Phoenix image but the e-ink controller
   code differs — prefer 1.2.2.
3. **Charge it** to full and keep it on USB power during flashing.
4. **Back up first.** A full 2 GB internal-storage image of a working device is
   the only real undo button:
   ```bash
   # with the device booted into NookManager/CWM, over adb:
   adb shell dd if=/dev/block/mmcblk0 | gzip > backups/nst-full-$(date +%F).img.gz
   ```
   Store backups **outside this repo** (see `.gitignore`) — they are 2 GB and may
   contain your B&N account data.

## Route A — Phoenix Project phase 4 (recommended)

Why: B&N killed the activation servers in June 2024, so a factory-reset stock
device can no longer be registered and stays half-crippled. Phoenix images are
CWM backups of devices that were *already* registered and lightly rooted, so
restoring one gives you a fully working, rooted, non-phoning-home device.

1. Read the thread: <https://xdaforums.com/t/nst-g-the-phoenix-project.4673934/>
   (Cloudflare blocks scripted fetches — open it in a browser.)
2. Download **`NST_Phase4_122.zip`** (FW 1.2.2 flavour) for BNRV300, or the
   GlowLight equivalent for BNRV350.
3. Write the bootable **CWM / NookManager** SD image to the microSD, using the
   **USB card reader with the card out of the Nook** — through the Nook you only
   see a mounted partition, and the device is using it.
   ```bash
   ./tools/flash-sd.sh downloads/<image>.img /dev/sdX
   ```
   That wrapper refuses anything that is not a removable USB whole-disk under
   64 GiB, and makes you retype the device name. Use it rather than a raw `dd` —
   the failure mode of a typo is overwriting your NVMe.
4. Copy the phase-4 zip onto that card's data partition.
5. Power the Nook **off**, insert the card, power on → it boots into recovery.
6. Restore / install the phase-4 image.
7. Remove the card, reboot. You should land on a rooted 1.2.2 system that
   includes **Nook Mod Manager (NMM)** and a file manager.

What phase 4 gives us: root, ADB, no B&N phone-home, NMM (screensaver banner
off, drag-to-unlock off, Home-button remapping) — exactly the settings the
dashboard apps want.

## Route B — NookManager (classic, still fine)

If you'd rather root your existing install than restore someone else's image:

1. Get a **1.2.2-capable** NookManager image. The stock v0.5.0 image fails on
   FW 1.2.2. The rebuild by XDA user *smjohn1*, incorporating nmyshkin's 1.2.2
   patches, is linked from
   <https://xdaforums.com/t/nookmanager-updated-for-1-2-2.3973967/>:

   ```bash
   mkdir -p downloads && curl -L -o downloads/NookManager1.2.2.img \
     "https://www.dropbox.com/s/kdlabh09txkx3k9/NookManager1.2.2.img?dl=1"
   ```

   | | |
   |---|---|
   | Size | 67,092,480 bytes (64 MiB) |
   | SHA-256 | `f33aca9eb9bc256e07399500c2a939815ca421ae090db265bbb98a5b63cc0253` |
   | Type | Unpartitioned FAT32, volume label `NookManager` |

   ### ⚠ The image is a filesystem, not a disk image

   This one costs an evening if you hit it blind. `NookManager1.2.2.img` has
   **no MBR partition table** — sector 0 is a FAT32 volume boot record
   (`OEM-ID "mkdosfs"`, all four partition entries zero). Written straight to
   the card with `dd if=... of=/dev/sdX`, the Nook:

   - boots (u-boot's `fatload mmc 0` happily reads a filesystem at sector 0),
   - shows the **NookManager splash and "loading..."**,
   - and then **hangs there forever**.

   The reason is in the boot ramdisk. `/sbin/system_ready` runs:

   ```sh
   mount -t vfat -o ro /dev/block/mmcblk1p1 /sdcard
   rsync ... /sdcard/ /tmp/sdcache
   /tmp/sdcache/hooks/system_ready
   ```

   With no partition table there is no `mmcblk1p1`, so the mount fails, nothing
   is copied to `/tmp/sdcache`, and the hook that would draw the menu never
   runs. E-ink holds the last frame, so a device that is actually alive looks
   frozen. `scripts/format_unused_sdcard` confirms the intended layout: **p1**
   is the NookManager filesystem and **p2** is created later in the free space
   to hold `backup.full.gz`.

   `tools/flash-sd.sh` detects this and does the right thing — it creates an MBR
   with p1 at sector 63 (`63,131040,c,*`) and writes the filesystem *into the
   partition*. On a 2 GB card that leaves ~1.75 GB free for the backup
   partition, which is enough for a gzipped image of the 2 GB internal storage.

   **Verify before flashing.** The image's root directory should contain
   `custom/ files/ hooks/ menu/ scripts/` — exactly matching doozan's upstream
   tree in `external/NookManager/NookManager/` — plus the OMAP first-stage
   bootloader `MLO` and `BOOT.SCR`. That correspondence is what makes it
   plausible; it is still a binary from a forum post, so treat it accordingly.

   > Note: this cannot be automated from a plain HTTP client. `doozan.com` is
   > 404, GitHub has no release assets, and the XDA thread that carries the link
   > is behind Cloudflare. Building from source is also out —
   > `external/NookManager/readme.md` requires a **32-bit Linux host** and
   > `build.sh` pulls a 2013 Buildroot from long-dead URLs.

   `downloads/` is gitignored.
2. `dd` the image to a microSD, boot from it, use the on-screen GUI:
   **Backup** first, then **Root My Nook**, and enable ADB.
3. Optionally install Nook Touch Mod Manager from the same menu.

Original thread: <https://forum.xda-developers.com/t/root-nookmanager-graphical-rooter-for-1-2-x-and-beyond.2040351/>

## After rooting — verify

```bash
adb devices              # device shows up
adb shell id             # uid=0(root) after `su`
adb shell getprop ro.build.version.release   # 2.1-update1
```

Enable ADB over Wi-Fi so we stop fighting the USB cable:
```bash
adb tcpip 5555
adb connect <nook-ip>:5555
```

## Settings worth flipping immediately

| Where | Setting | Why |
|---|---|---|
| Settings → Wireless | Wi-Fi always on | Otherwise it drops the network in sleep |
| Settings → Display → Screensaver | point at our image dir, 2 min | Deep-sleep display trick |
| NMM | Hide screensaver banner | Removes the "Touch to wake" overlay |
| NMM | Disable drag-to-unlock | Panel wakes straight to the image |
| NMM | Home button → our app | One-button recovery when it wedges |

## Recovery / un-bricking

The NST tries to boot from SD first, so a bad internal install is almost always
recoverable by booting a NookManager/CWM card and restoring a backup. **Eight
failed boots** in a row trigger B&N's factory reset. Keep one known-good SD card
and one known-good `.img.gz` and you effectively cannot brick this thing.

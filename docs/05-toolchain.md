# 05 — Toolchain and workstation setup

Host assumed: Linux (this repo lives on one).

## ADB

```bash
sudo apt install android-tools-adb android-tools-fastboot   # or platform-tools zip
adb devices
```

Udev rule so we don't need `sudo` (B&N vendor id `2080`):
```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2080", MODE="0666", GROUP="plugdev"' \
  | sudo tee /etc/udev/rules.d/51-nook.rules
sudo udevadm control --reload-rules
```

ADB over Wi-Fi (much nicer for a wall-mounted device):
```bash
adb tcpip 5555
adb connect <nook-ip>:5555
```

## Writing SD images

```bash
lsblk                      # identify the card. Twice. Slowly.
sudo dd if=image.img of=/dev/sdX bs=4M status=progress conv=fsync
sync
```

## Building an Android 2.1 (API 7) app

Modern Android Studio cannot target API 7. Options, best first:

1. **Copy the TRMNL client's build setup.** It is a maintained project that
   builds a working API-7 APK in 2026 — read `external/trmnl-nook-simple-touch`.
2. **Old SDK route:** `platforms/android-7` + old `build-tools`, driven by a
   Makefile calling `aapt` → `javac -source 1.6 -target 1.6` → `d8`/`dx` →
   `apksigner`. Sign with any debug key; the device doesn't care.
3. Avoid AndroidX, Gradle plugin defaults, and anything expecting `minSdk >= 14`.

Install:
```bash
adb install -r app.apk
# or, unrooted-friendly: copy to /media/My Files and tap it in ES File Explorer
```

## Native ARM binaries

- **Android NDK r12b** — newer NDKs produce binaries that segfault on this
  device's bionic. Pin it.
- Target `armeabi-v7a`, `android-9` or below.
```bash
adb push hello /data/local/tmp/ && adb shell chmod 755 /data/local/tmp/hello \
  && adb shell /data/local/tmp/hello
```

## Custom kernel (only if we do the kernel side-quest)

`external/nst-kernel` needs a **pre-2014 GCC ARM cross-compiler**; modern
toolchains refuse to build Linux 2.6.29. Practical approach: build inside an
old-distro Docker container (e.g. Debian jessie/wheezy image with
`gcc-arm-linux-gnueabi`).

## Server side (the part that does the work)

Anything you like. Suggested minimum for our own dashboard:
```
python3 -m venv .venv && . .venv/bin/activate
pip install fastapi uvicorn jinja2 pillow requests
# optional, for HTML→PNG rendering:
pip install playwright && playwright install chromium
```
Render at exactly **800×600**, greyscale, and dither with Pillow before serving.

## Useful on-device bits

| Thing | Note |
|---|---|
| Nook Mod Manager (NMM) | Screensaver/banner/unlock/button remapping. Ships with Phoenix phase 4 |
| ES File Explorer | Included in phase 4; how you tap-install APKs without ADB |
| F-Droid | Only realistic app store; the Play Store is effectively dead here |
| Dev settings password (Glowlight-4 style menus) | `NOOK-BNRV1100` — noted in the TRMNL docs, model-dependent |
| NoRefresh / FastMode | 1-bit mode for faster refresh |

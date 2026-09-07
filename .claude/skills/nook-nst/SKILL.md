---
name: nook-nst
description: Working on the Nook Simple Touch (BNRV300/BNRV350) e-ink hacking project in this repo — rooting, ADB, Android 2.1 (API 7) app development, e-ink refresh and deep sleep, dashboard servers rendering 800x600, custom kernels, and the docs/lab-log conventions. Use whenever the task mentions the Nook, NST, e-ink display, Phoenix Project, NookManager, TRMNL client, ElectricSign, or adding an upstream project to external/.
---

# Nook Simple Touch project

## Hard facts (don't re-derive these)

- **BNRV300** = Nook Simple Touch; **BNRV350** = with GlowLight. Target firmware **1.2.2**.
- OMAP3621 Cortex-A8 800 MHz, **256 MB RAM**, **Android 2.1 (API level 7)**, Linux 2.6.29.
- Display **800×600**, 16-level greyscale E Ink Pearl. Full refresh ~800 ms and flashes.
- Wi-Fi 2.4 GHz b/g/n only. **No Bluetooth.** No Play Services, no working Play Store.
- Android 2.1's TLS stack **cannot do TLS 1.2 / SNI** → the stock browser can't
  open the modern web. Work around it with plain HTTP on the LAN, or by bundling
  **BouncyCastle** in our own app (as the TRMNL client does).
- B&N shut the servers in **June 2024**; stock devices can't register. The
  **Phoenix Project phase 4** CWM image is the current rooting path — its phases
  are alternatives, not sequential steps.
- **No postmarketOS / mainline Linux port exists.** A real distro is only
  possible as a slow chroot. Don't propose native Linux as a step.
- Native ARMv7 ELF binaries work, but only when built with **Android NDK r12b** —
  newer NDKs segfault on this bionic.

## Architecture rule for this project

**Render off-device.** A server produces an 800×600 image (or trivial HTML); the
Nook fetches, displays, and sleeps. Never put API calls, TLS, or layout work on
the device unless we are deliberately doing the write-our-own-app side-quest.

Deep sleep = write the image as the **screensaver**, set an `AlarmManager` RTC
wakeup, turn Wi-Fi off. ~30+ days battery at a 30-minute refresh, vs ~60 h awake.

## This device

**BNRV300, firmware 1.2.2** — the exact config the modern tooling targets.
Root with Phoenix Project **phase 4, `NST_Phase4_122.zip`**.

## Our two components

- `app/` — **NookPanel**, our API-7 client. Build with `cd app && make debug`
  (uses `nook-adt` Docker image: 2014 ADT bundle + Ant + JDK 8; nothing modern
  can target API 7). Compile target is `android-20` because that is all the
  bundle ships; runtime target is API 7 via `uses-sdk`. Java 6 language level —
  no diamond operator, no try-with-resources.
- `server/` — renders a 600x800 greyscale PNG (clock + Open-Meteo weather) and
  serves it over plain HTTP for a Pi Zero 2 W. `python3 panel_server.py --once
  out.png` renders a single frame for inspection.

**Deep sleep, the one trick that works:** set
`Settings.System.SCREEN_OFF_TIMEOUT` to ~1000 ms (needs only the normal
`WRITE_SETTINGS` permission) and let Android's own `PowerManagerService` run the
screen-off path. `PowerManager.goToSleep`, `input keyevent 26`, raw `sendevent`,
`echo mem > /sys/power/state` and `service call power` all fail — the details
are in `docs/06-our-own-app.md`.

## Repo conventions

- `docs/` — numbered docs, index in `docs/README.md`. **Every session that
  touches hardware gets an entry appended to `docs/99-lab-log.md`** using the
  template at the top of that file.
- `external/` — upstream projects **as git submodules only**. Never vendor, never
  edit in place. Adding one:
  ```bash
  git submodule add <url> external/<name>
  ```
  and add a row to the table in `external/README.md` saying *why we care*.
- Device backups, firmware zips, APKs and secrets are gitignored — keep 2 GB
  device images out of the repo.
- Anything learned from upstream source goes into `docs/`, not into memory.

## Before touching the device

1. Confirm model + firmware (Settings → Device Info) and record them in the lab log.
2. Take a full backup before any flash:
   `adb shell dd if=/dev/block/mmcblk0 | gzip > backups/nst-full-$(date +%F).img.gz`
3. When writing SD cards, run `lsblk` and confirm the target twice — a wrong
   `dd` target destroys the host disk.
4. Recovery: the NST boots SD first, so a NookManager/CWM card + a backup makes
   it effectively unbrickable. Eight failed boots trigger B&N's factory reset.

## Common commands

```bash
adb devices
adb tcpip 5555 && adb connect <nook-ip>:5555   # ADB over Wi-Fi
adb install -r app.apk
adb push bin /data/local/tmp/ && adb shell chmod 755 /data/local/tmp/bin
adb shell getprop ro.build.version.release      # expect 2.1-update1
```

## When asked "can it do X?"

Check the constraints above first, and give an honest verdict with the effort
level, rather than an enthusiastic yes. Refer to
`docs/03-linux-and-custom-code.md` (what's possible) and
`docs/04-project-ideas.md` (ranked ideas, plus what is a bad fit).

## Key upstream references

- `external/trmnl-nook-simple-touch` — the maintained API-7 app to copy patterns from.
- `external/nook-dashboard` — Home Assistant/calendar/weather 800×600 server.
- `external/Nook-weather-NWS` — no-API-key weather page.
- `external/NookManager` — classic SD graphical rooter.
- Phoenix Project thread (read in a browser; Cloudflare blocks fetching):
  <https://xdaforums.com/t/nst-g-the-phoenix-project.4673934/>

# 03 — "Can we run Linux and write our own app?"

Short answers first, then the evidence.

| Question | Answer |
|---|---|
| Can we run Linux? | **Technically yes, practically no.** It already *is* Linux (Android 2.1 = Linux 2.6.29). A real distro only exists as a **chroot** on top of Android; nobody has a usable native distro or postmarketOS port. |
| Can we write our own app? | **Yes, comfortably.** Android 2.1 / API 7 Java apps still build and run — the TRMNL client is actively maintained proof. |
| Can we write bare native code? | **Yes.** Static ARMv7 ELF binaries drawing straight to `/dev/graphics/fb0` work, with NDK **r12b**. |
| What *should* we do? | Server renders an 800×600 image; a small on-device app displays it and sleeps. |

---

## Option 1 — Server-rendered image + dumb client ⭐ recommended

The Nook runs one app whose entire job is: wake → fetch a PNG over the LAN →
draw it fullscreen → sleep until the next alarm. All logic (weather API,
calendar, Home Assistant, layout, fonts) lives on a server we control.

- Dodges the TLS-1.2 problem (plain HTTP on our own LAN, or the client's
  bundled BouncyCastle).
- 256 MB RAM and an 800 MHz A8 never have to render anything.
- We can iterate on the design in seconds without touching the device.
- Battery: **30+ days** with deep sleep at a 30-minute refresh, versus ~60 h
  awake. That number comes from the TRMNL client's own measurements.

Existing clients we can use as-is: **TRMNL client in BYOS mode**, or
**ElectricSign**. Existing servers: `nook-dashboard`, `Nook-weather-NWS`.

## Option 2 — Write our own Android app

Perfectly viable, and the right move once we want touch interaction, local
caching, or our own sleep policy.

Constraints:
- `compileSdk`/`minSdk` **7** (`android-7`). Modern Android Studio + AGP cannot
  target this; use an old SDK build-tools chain or plain `aapt`/`javac`/`d8`
  invoked from a Makefile. Read `trmnl-nook-simple-touch`'s build files — they
  have already solved this exact problem.
- No AndroidX, no Kotlin coroutines-era libraries, no `HttpURLConnection` TLS
  1.2 — bundle **BouncyCastle** if you must speak HTTPS.
- E-ink API: B&N exposes refresh control via `android.hardware.EpdController`
  (undocumented, reflection-accessed) plus `/sys/class/graphics/fb0/epd_*`.
  Grep the TRMNL client for how it forces full vs partial refresh.
- Deep sleep is done by writing the image as the **screensaver** and setting an
  `AlarmManager` RTC wakeup, then turning Wi-Fi off — again, copy TRMNL.

## Option 3 — Native C/C++ on the framebuffer

The purist route, documented well by
[badd10de](https://badd10de.dev/notes/nook-simple-touch.html):

- Device runs **32-bit ARMv7 ELF** binaries; push them with `adb push`, mark
  `chmod 755`, run from `adb shell`.
- Use **Android NDK r12b** specifically — newer NDKs produce binaries that
  segfault on this bionic.
- Draw into `/dev/graphics/fb0` (16 bpp RGB565 that the e-ink controller
  converts to greyscale), then trigger a refresh via the EPD sysfs entries.
- Someone has run **PyGame/SDL** this way, so the path is real.

Good for a genuinely custom clock with no Android overhead. Bad for anything
that needs Wi-Fi, TLS, or fonts you didn't bring yourself.

## Option 4 — A real Linux distro in a chroot

- The only documented attempt: [Hackaday project
  #163769](https://hackaday.io/project/163769-nook-simple-touch-tweaked-to-run-linux-distros)
  — Ubuntu 10.10 in a chroot, displayed over **VNC**, with swap on SD to survive
  256 MB of RAM. The author never got X onto the e-ink panel.
- Modern equivalent: a Debian armel/armhf rootfs + `chroot` from a root shell,
  driven over SSH. Note **armel** — this SoC is fine with armhf (Cortex-A8 has
  VFPv3) but Debian dropped armel/armhf for old kernels; you'd need an ancient
  Debian release or Alpine armhf. This is a weekend of yak-shaving for a shell
  we could get with `adb shell` + BusyBox anyway.

**Verdict: skip it**, unless the goal is the journey.

## Option 5 — Native Linux boot / postmarketOS

- B&N released GPL kernel sources; [`nst-kernel`](https://github.com/felixhaedicke/nst-kernel)
  is those sources plus USB-host and fast-display patches, and the device boots
  u-boot from SD, so **replacing the kernel is genuinely easy**.
- But: the tree is **Linux 2.6.29**, it needs an **ancient GCC cross-compiler**
  (modern gcc won't build it), and there is **no mainline OMAP3621 + E Ink
  display support** for this panel. No postmarketOS port exists.
- Porting means writing a mainline e-ink framebuffer driver for a 2011 panel.
  That is a real research project, not a step in this one.

**Verdict: out of scope**, but `nst-kernel` is still interesting for two
concrete wins: **USB host mode** (plug in a keyboard or USB ethernet) and
**fast 1-bit display mode**.

---

## Our path

1. Root via Phoenix phase 4.
2. Ship something visible fast with an existing client + our own server.
3. Then write our own Android 2.1 app, using the TRMNL client as the reference
   for build chain, e-ink control, and deep sleep.
4. Optional side-quests: native framebuffer binary, custom kernel for USB host.

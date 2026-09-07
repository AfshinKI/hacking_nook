# 01 — What people have already done

Research snapshot: **September 2026**. Sources are linked inline; anything on
xdaforums.com blocks automated fetching, so those were read via search summaries
and should be re-read by hand before following exactly.

## The community, in one paragraph

The NST hacking scene peaked on XDA around 2012–2014 (NookManager, TouchNooter,
Nook Touch Mod Manager, custom kernels, overclocking, USB host). It went quiet,
then came back to life after **Barnes & Noble's June 2024 end-of-life**, because
suddenly a lot of people had bricked-ish e-readers and nothing to lose. The
current centre of gravity is the **Phoenix Project** (rooted firmware images) plus
the **TRMNL Nook client** (a maintained, modern Android 2.1 app — proof that
building our own app is realistic).

## Rooting toolchain — three generations

| Tool | Era | What it is | Status |
|---|---|---|---|
| TouchNooter | 2011–12 | SD-card autorooter | Obsolete |
| [NookManager](https://github.com/doozan/NookManager) | 2013 | Bootable SD image with a GUI: backup, root, install ADB/Gapps/NTMM. 94★, last commit 2013 | Works, but stumbles on FW 1.2.2 without the community patch |
| **[Phoenix Project](https://xdaforums.com/t/nst-g-the-phoenix-project.4673934/)** | 2024– | Set of **CWM restore images** of already-rooted, already-provisioned devices. Bypasses B&N's dead registration servers entirely | **Current recommended path** |

Phoenix "phases" are independent alternatives, *not* sequential steps — this
confuses everyone. **Phase 4** = minimal rooted FW 1.2.2 or 1.1.5 image with
Nook Mod Manager included, aimed at people who want to customise. That is ours.

## The display-something-on-it projects

| Project | What | Notes |
|---|---|---|
| **[usetrmnl/trmnl-nook-simple-touch](https://github.com/usetrmnl/trmnl-nook-simple-touch)** (MIT, active — commits Aug 2026) | Android 2.1 client that fullscreen-displays an image from the TRMNL service **or your own server (BYOS)** | The single most valuable reference in the whole ecosystem. Bundles BouncyCastle for TLS 1.2, does deep sleep via RTC alarm + screensaver trick (**30+ days** battery vs ~60 h), reports battery/RSSI. Has a **WebUSB browser installer** at `nooks.bpmct.net/manage/` |
| [usetrmnl/trmnl-nook](https://github.com/usetrmnl/trmnl-nook) | Same idea for the **Glowlight 4**, not the NST | Useful only for the ADB/dev-settings tricks |
| **ElectricSign** (Play Store app, `com.sugoi.electricsign`) | Renders a URL to PNG and shows it fullscreen on a timer | The classic "dumb panel" app. Play Store is hard to get on NST now — sideload the APK |
| [greghare/nook-dashboard](https://github.com/greghare/nook-dashboard) (53★, active 2026) | Python/Flask server that renders a **Home Assistant + calendar + weather + to-do** page at 800×600 for ElectricSign | Best starting point for a HA-integrated dashboard |
| [TheCase/nook-weather](https://github.com/TheCase/nook-weather) | Dockerised 800×600 weather page (Wunderground-era) | Older, but tiny and readable |
| [Home-Is-Where-You-Hang-Your-Hack/Nook-weather-NWS](https://github.com/Home-Is-Where-You-Hang-Your-Hack/Nook-weather-NWS) (MIT, active) | Rewrite of the above in TypeScript using free **NOAA/NWS** data | Good if you want no API keys |
| [Nirmal Kumar's info display](https://nkdews.me/creating-a-information-display-using-old-e-ink-reader-nook/) | Blog build log: rooted NST + Electric Sign as a wall news panel | Realistic end-to-end walkthrough |

## The go-deeper projects

| Project | What |
|---|---|
| **[felixhaedicke/nst-kernel](https://github.com/felixhaedicke/nst-kernel)** (GPL-2.0) | Kernel from B&N's GPL sources + staylo's patches: **USB host mode** fix and **fast (1-bit) display mode**. This is how you get USB keyboards/ethernet and snappier refresh |
| [rychly/nst-linux-sources](https://github.com/rychly/nst-linux-sources) | Mirror of B&N's kernel source for the Glowlight variant |
| [badd10de's NST notes](https://badd10de.dev/notes/nook-simple-touch.html) | The best low-level write-up: rooting, mounting/repacking the boot `uramdisk`, and **running plain ARM ELF binaries** written in C against `/dev/graphics/fb0`. Warns that only **Android NDK r12b** works; newer NDKs segfault |
| [PyGame on the NST](http://orbitalfruit.blogspot.com/2018/12/pygame-on-nook-simple-touch.html) | Yes, someone ran Python + SDL on it |
| [Hackaday: NST running Linux distros](https://hackaday.io/project/163769-nook-simple-touch-tweaked-to-run-linux-distros) | Ubuntu 10.10 in a **chroot** on top of Android, accessed over **VNC**. Incomplete; never got X on the panel |
| NoRefresh / FastMode | Long-standing app/kernel trick: drop to 1-bit depth for near-video refresh rates |

## What does *not* exist (checked)

- **No postmarketOS / mainline Linux port** for BNRV300/BNRV350. Nobody has done it.
- **No modern Android** (no LineageOS, no CyanogenMod build that matters).
- **No working Google Play Store** in 2026 — use F-Droid or plain sideloading.

Sources: see links above, plus
[How-To Geek: ways to repurpose your old Nook](https://www.howtogeek.com/ways-to-repurpose-your-old-nook-ereader/),
[Wikipedia: Nook Simple Touch](https://en.wikipedia.org/wiki/Nook_Simple_Touch).

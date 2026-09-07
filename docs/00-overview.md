# 00 — Overview: the device and the goal

## Goal

Turn a Nook Simple Touch (NST) e-reader into a useful, always-on, wall-mountable
e-ink information display (clock / calendar / weather / home dashboard), and
learn how far we can push the hardware (custom apps, native code, Linux).

## The hardware

| | |
|---|---|
| Model | Nook Simple Touch **BNRV300** (2011) / **BNRV350** with GlowLight (2012) |
| SoC | TI OMAP3621, ARM Cortex-A8 @ 800 MHz (overclockable ~1 GHz with custom kernel) |
| RAM | 256 MB |
| Storage | 2 GB internal + microSD slot |
| Display | 6" E Ink Pearl, **800×600**, 16-level greyscale |
| Touch | Infrared (Neonode) touch frame — **no capacitive digitizer** |
| Wi-Fi | 802.11 b/g/n 2.4 GHz only. **No Bluetooth.** |
| OS | **Android 2.1 Eclair (API level 7)** |
| Power | microUSB. Weeks-to-months of battery when sleeping between refreshes |

## Why this device is interesting

- ~$25–40 used on eBay; e-ink at 800×600 is still a nice dashboard panel.
- Draws almost no power: the panel only costs energy when it *changes*.
- It is a full Android device, so we can install and write real apps —
  unlike most cheap e-ink frames.

## Why it is awkward (read this before planning anything)

1. **Android 2.1 / API 7.** Modern Android Studio can't target it. No Play
   Services, no Play Store, no modern APK will install. We compile against a very
   old SDK, or we don't compile at all.
2. **TLS is dead on-device.** Android 2.1's stack can't do TLS 1.2 / modern
   ciphers / SNI, so the stock browser cannot open most of today's web. Apps work
   around this by bundling **BouncyCastle** (this is exactly what the TRMNL
   client does) — or by talking only to a **local, plain-HTTP server on our LAN**.
3. **B&N end-of-life, June 2024.** Barnes & Noble shut down the servers for
   2013-and-earlier Nooks. A stock, un-hacked device keeps trying to phone home,
   which wastes battery; device *registration* is no longer possible the normal
   way. This is precisely what the **Phoenix Project** images fix — see
   [02-rooting.md](02-rooting.md).
4. **E-ink refresh.** Full refreshes are ~800 ms and flash black. Partial /
   "fast mode" (1-bit) updates exist but need kernel or app-level tricks
   (NoRefresh / FastMode). Do not design anything that animates.

## Design conclusion we start from

**Do the thinking off-device.** The Nook should be a dumb-ish panel that fetches
a pre-rendered 800×600 image (or a very simple local HTML page) from a server we
control on the LAN — a Raspberry Pi, a NAS, or this laptop. That single decision
sidesteps TLS, CPU, RAM, and API-level problems all at once. Everything
"clever" (calendar APIs, weather APIs, Home Assistant) runs on the server.

See [04-project-ideas.md](04-project-ideas.md) for the ranked build list and
[03-linux-and-custom-code.md](03-linux-and-custom-code.md) for how deep the
rabbit hole goes.

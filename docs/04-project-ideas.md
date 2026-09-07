# 04 — What we could build, ranked

Scored on: **value** (would we actually look at it daily), **effort**, and
**risk** (chance it dead-ends on Android 2.1).

## Tier 1 — do these

### 1. LAN dashboard panel: clock + date + weather + calendar ⭐ the target
Server renders 800×600 PNG; Nook displays and sleeps. This is the thing you
asked for, and it is a solved problem — we just need to make it *ours*.
- Effort: low. Risk: low. Battery: 30+ days.
- Reuse: [`nook-dashboard`](https://github.com/greghare/nook-dashboard) if you
  run Home Assistant; [`Nook-weather-NWS`](https://github.com/Home-Is-Where-You-Hang-Your-Hack/Nook-weather-NWS)
  if you want a no-API-key weather page; otherwise a ~150-line Flask/FastAPI app
  of our own with Open-Meteo + a CalDAV/ICS feed.

### 2. Our own Android 2.1 display client
Once #1 works with an off-the-shelf client, replace the client with ours so we
control refresh policy, error screens, offline caching, and the config UI.
- Effort: medium. Risk: low — the TRMNL client proves every hard part is solved.

### 3. Deep-sleep power tuning
Screensaver-as-display + `AlarmManager` RTC wake + Wi-Fi off. Turns "a tablet
plugged into the wall" into "a battery gadget you charge monthly".
- Effort: low, big payoff, and it is mostly *settings*.

## Tier 2 — good follow-ups

### 4. Touch interaction
The IR touch frame works. A tap could cycle pages (weather → calendar → transit
→ photo), a long-press could force refresh. Cheap once we own the app.

### 5. Photo / art frame
Server picks an image, dithers it to 16-level greyscale (Floyd–Steinberg via
Pillow), Nook shows it. Genuinely lovely on e-ink.

### 6. Home Assistant panel with controls
Read-only is easy; making buttons that *do* things means POSTing back to HA
from the device — fine over plain HTTP on the LAN.

### 7. Offline reading rig, done properly
It is still an excellent e-reader: KOReader, Calibre-Web / OPDS over LAN,
Wallabag-style read-later. Low effort, high daily value.

### 8. Server-side "any website → e-ink" renderer
Headless Chromium on the server, 800×600 viewport, greyscale + dither, serve
PNG. This makes the modern web viewable on a device whose TLS stack died a
decade ago — the ElectricSign idea, but done on hardware that can afford it.

## Tier 3 — the fun rabbit holes

### 9. Native C framebuffer app
A no-Android clock drawing straight to `/dev/graphics/fb0` with NDK r12b.
Satisfying; not useful.

### 10. Custom kernel (`nst-kernel`)
USB host mode (keyboard, USB ethernet) and fast 1-bit display mode. Needs an
ancient cross-compiler. Real payoff if we ever want a keyboard-driven device.

### 11. Debian chroot
Documented, slow, and mostly pointless — `adb shell` + BusyBox gives us the
shell we actually wanted. See [03](03-linux-and-custom-code.md).

### 12. Not-a-project: postmarketOS port
No port exists. Would require a mainline e-ink driver. Out of scope.

## Ideas that are *bad* on this hardware

- Anything animated or video — e-ink refresh is ~800 ms full-screen.
- Anything needing modern HTTPS **directly from the device's browser**.
- Anything needing Bluetooth (there is none) or 5 GHz Wi-Fi (there is none).
- Anything needing the Play Store or Play Services.

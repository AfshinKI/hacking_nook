# hacking_nook

A **Nook Simple Touch** (2011 e-reader, 800×600 e-ink, Android 2.1) turned into
a wall dashboard. A Raspberry Pi draws the page; the Nook fetches and displays
it, then sleeps.

<!-- What it looks like: docs/06-our-own-app.md and upstream/README.md -->

## How it fits together

```
Raspberry Pi                                     Nook Simple Touch
┌──────────────────────────────────────┐         ┌──────────────────┐
│ weather-cal  :8082                   │         │ NookPanel app    │
│   draws 4 pages, once an hour        │         │   fetches the    │
│         │                            │  wifi   │   PNG every 5m   │
│         ▼                            │ ──────► │   and displays   │
│ nookpanel    :8000                   │         │   it fullscreen  │
│   picks which page, serves the PNG   │         └──────────────────┘
└──────────────────────────────────────┘
```

Both services run **on the Pi**. Nothing else is needed once deployed — no
desktop, no cloud, no API keys.

- **weather-cal** is [chrisjtwomey/inkplate10-weather-cal](https://github.com/chrisjtwomey/inkplate10-weather-cal)
  run as-is, with one file swapped so its map comes from OpenStreetMap instead
  of Google. It renders HTML in headless Chromium — slow, hence hourly.
- **nookpanel** picks which of the four pages to show, on every refresh, from
  the time of day and the incoming weather. Fast, hence every 5 minutes.
- **NookPanel** (the app) is ours, built for Android 2.1, which nothing modern
  can target.

## Set up the server (Raspberry Pi)

Any Pi running Raspberry Pi OS. Tested on a **Zero 2 W** — 425 MB of RAM, which
is the tight case.

```bash
sudo apt install -y git
git clone https://github.com/AfshinKI/hacking_nook.git ~/hacking_nook
cd ~/hacking_nook

# 1. the page renderer (chromium, ~10 min, raises swap to 2 GB)
OSM_MAP_LABEL="Your City" ./upstream/install-on-pi.sh

# 2. the panel server
./server/install-on-pi.sh

# 3. your location
nano server/config.json          # latitude, longitude, timezone
nano upstream/run/config.yaml    # location:, timezone:
sudo systemctl restart weather-cal nookpanel
```

Both install as systemd units, **enabled at boot** — after a power cut the Pi
comes back on its own with no intervention.

```bash
systemctl status weather-cal nookpanel
journalctl -u weather-cal -f
curl -o test.png http://localhost:8000/panel.png
```

Give the Pi a **DHCP reservation**. The Nook stores a literal URL, and typing
one on an infrared touchscreen is miserable.

## Set up the Nook

1. **Root it.** NookManager from an SD card — [docs/02-rooting.md](docs/02-rooting.md).
   Back up from its menu *before* rooting.
2. **Build and install the app** (needs Docker on any x86_64 machine, once):
   ```bash
   cd app && make image && make debug
   adb install -r bin/NookPanel-debug.apk
   ```
3. **Point it at the Pi**, over adb rather than the touchscreen:
   ```bash
   ./tools/push-config.sh http://<pi-ip>:8000/panel.png 300
   ```
4. It starts itself on boot. Tap the screen for Refresh / Settings.
   [`./tools/screenshot.sh out.png`](tools/screenshot.sh) shows you the panel
   from your desk.

Full detail, and the Android-2.1 traps: [docs/06-our-own-app.md](docs/06-our-own-app.md).

## Change what it shows

| Want to | Do |
|---|---|
| Different page times | `page_schedule` in `server/config.json` |
| Different map framing | `OSM_MAP_ZOOM` / `OSM_MAP_CENTER` — [upstream/README.md](upstream/README.md) |
| Your own map picture | `OSM_MAP_FILE=/path/to.png` |
| Turn off weather alerts | `"advisories": false` |
| Skip weather-cal entirely | unset `renderer_url`; `server/` draws its own simpler pages |

## Layout

```
app/         NookPanel — our Android 2.1 client
server/      picks and serves the page; can also draw its own
upstream/    weather-cal: our OSM map shim, patches, Pi installer
tools/       flash an SD card, push config, screenshot the panel
docs/        how it was built, and the lab log
external/    upstream projects as submodules — never edited in place
```

Start with [docs/README.md](docs/README.md).

## Third-party code and data

Nothing is vendored — upstream projects are submodules, so this repo carries
only pointers and our own code.

| What | Licence |
|---|---|
| `inkplate10-weather-cal` (run, plus one patch in `upstream/patches/`) | MIT, © 2023 Chris Twomey |
| `trmnl-nook-simple-touch`, `Nook-weather-NWS` (reference) | MIT |
| `nook-dashboard`, `NookManager` (reference) | no licence stated upstream |
| Map data, fetched at runtime | © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright) |
| `app/res/drawable-*/ic_launcher.png` (Android SDK template) | Apache-2.0 |
| Comic Neue (from Debian, not vendored) | SIL OFL |

Rooting images and device backups are **not** in this repo and must not be.

```bash
git clone --recurse-submodules https://github.com/AfshinKI/hacking_nook.git
```

# external/ — upstream projects as submodules

Every third-party GitHub project we reference lives here as a **git submodule**,
so this repo records the exact commit we read without vendoring anyone's code.

```bash
git submodule update --init --recursive
```

| Path | Upstream | Why we care |
|---|---|---|
| `trmnl-nook-simple-touch` | [usetrmnl/trmnl-nook-simple-touch](https://github.com/usetrmnl/trmnl-nook-simple-touch) (MIT) | The reference maintained Android 2.1 app: API-7 build chain, BouncyCastle TLS 1.2, e-ink refresh, deep-sleep-via-screensaver. Our model for writing our own client |
| `nook-dashboard` | [greghare/nook-dashboard](https://github.com/greghare/nook-dashboard) | Python server rendering an 800×600 Home Assistant + calendar + weather page for ElectricSign |
| `Nook-weather-NWS` | [Home-Is-Where-You-Hang-Your-Hack/Nook-weather-NWS](https://github.com/Home-Is-Where-You-Hang-Your-Hack/Nook-weather-NWS) (MIT) | Dockerised 800×600 weather page using free NOAA/NWS data — no API keys |
| `NookManager` | [doozan/NookManager](https://github.com/doozan/NookManager) | The classic SD-card graphical rooter (2013). Historical/backup rooting route |

## Not added by default (add on demand)

Large or niche; add only when the matching side-quest starts:

```bash
git submodule add https://github.com/felixhaedicke/nst-kernel.git external/nst-kernel
git submodule add https://github.com/TheCase/nook-weather.git external/nook-weather
```

- `nst-kernel` (GPL-2.0) — B&N kernel sources + USB-host and fast-display
  patches. Full kernel tree, needs a pre-2014 GCC cross-compiler.
- `nook-weather` — older, very small Docker weather page; readable reference.

## Rules

- **Never edit files inside `external/`.** Fork upstream if we need changes.
- When an upstream project teaches us something, write it into `docs/`, don't
  rely on remembering where in their source it was.

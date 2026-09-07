# 07 — Hardware checklist and the order of operations

Device confirmed: **BNRV300, firmware 1.2.2** — the exact configuration the
modern tooling targets. Good news: no GlowLight quirks, no 1.1.5 e-ink
differences.

## Blocking prerequisites

| Need | Why | Status |
|---|---|---|
| **microSD card, 2–32 GB** + a reader | Phoenix/NookManager boot from SD. There is **no way to root without one** — the NST has no fastboot and no unlocked recovery. Cards >32 GB often fail; 4–8 GB is the sweet spot | ❓ do we have one? |
| `adb` on the workstation | Everything after rooting | ❌ not installed |
| A working microUSB **data** cable | Charge-only cables are the classic time-waster | ❓ see below |
| Somewhere to keep a 2 GB backup image | Off-repo, gitignored | ✅ |

## USB: the Nook is not currently visible

With the device plugged in, `lsusb` shows **no Barnes & Noble device**
(vendor id `2080`) and `lsblk` shows no ~2 GB volume. A stock NST enumerates as
USB mass storage as soon as it is connected and awake. So one of:

1. The cable is **charge-only** — swap it for a known data cable.
2. The Nook is asleep or off — wake it, then reconnect.
3. It is plugged into a hub that is not passing through — try a direct port.

Re-check with:
```bash
lsusb | grep -i 2080      # expect: ID 2080:0003 Barnes & Noble
lsblk                     # expect a ~1.2 GB removable volume
```

Nothing else can proceed until this works.

## Install adb

```bash
sudo apt install -y android-tools-adb
```
Then the udev rule from [05-toolchain.md](05-toolchain.md) so it works without
`sudo`.

## Order of operations

1. **Fix USB visibility.** (above)
2. **Install adb.**
3. **Get a microSD card.**
4. **Back up.** Before anything is written to the device. See
   [02-rooting.md](02-rooting.md).
5. **Root** with Phoenix Project **phase 4, FW 1.2.2 flavour**
   (`NST_Phase4_122.zip`) — matches this device exactly.
6. **Verify:** `adb devices`, `adb shell id` → uid 0.
7. **Bring up the server** on the Pi Zero 2 W ([../server](../server)) and
   confirm `http://<pi>:8000/panel.png` renders in a desktop browser.
8. **Install NookPanel:** `cd app && make debug && make install`, point it at
   the Pi's URL, watch it draw.
9. **Then** v0.2 deep sleep — see [06-our-own-app.md](06-our-own-app.md).

Steps 7 and 8's server half is **already done and testable today** without the
Nook: run the server and open `http://localhost:8000/` in a browser.

## Things that are not blockers

- No Wi-Fi credentials needed on the workstation side; the Nook joins your LAN
  itself once rooted (`Settings → Wireless`).
- No Google account, no Play Store, no B&N account — Phoenix phase 4 ships
  pre-provisioned precisely so we never touch B&N's dead servers.

# app — NookPanel, our Android 2.1 client

A fullscreen image panel for the Nook Simple Touch: fetch a PNG from a server on
the LAN, save the dashboard as the screensaver, and sleep until the next update.
The default refresh interval is **3600 seconds (one hour)**.

Long press the picture or status message to open the Refresh now / Settings menu.
An ordinary tap does not open the menu.

A small battery icon and percentage overlay the top-right corner of the image.
A plus sign indicates charging. The indicator uses the Nook's battery level,
updates only when its displayed state changes, and remains over a retained image
after a failed refresh. Long pressing it opens the same menu.

When an image URL is configured, NookPanel starts automatically after boot,
turns on the display, and dismisses the Nook's slide lock without a button press.
Automatic updates return to sleep after five seconds. Manually wake the Nook
with its physical wake button, then long press for the menu. It stays awake for
60 seconds after your last interaction; an open menu or Settings keeps it awake.
Side-button remapping and touch disabling are not needed.

If a refresh fails, the last successfully displayed image stays visible while
the app retries at the configured interval. An error is shown only if no image
has loaded yet. The last good image is saved in app-private storage so it also
survives app restarts and temporary network outages.

While asleep, the dashboard and battery snapshot remain visible. Wi-Fi is off;
an Android RTC wake alarm starts the next refresh even if the app process was
killed. Wi-Fi gets up to 25 seconds to reconnect and the whole fetch attempt has
a 75-second watchdog, after which the app retains the old image and sleeps.
Remote ADB over Wi-Fi is therefore available only while the device is awake.

The app selects `/media/screensavers/NookPanel/panel.png` and hides the Nook's
screensaver banner. This replaces the Innovetron “Resting” picture during normal
dashboard sleep; custom boot and power-off pictures still apply. The previous
screensaver selection is saved in app preferences. A failed screensaver write
retains the previous file. The temporary one-second screen timeout is restored
as soon as the screen turns off and recovered on the next launch after a crash.

```bash
make image     # one-time: build the pinned 2014 ADT container
make debug     # -> bin/NookPanel-debug.apk
make install   # adb install -r  (run on the host, Nook plugged in)
```

`make debug` always performs a clean build: the legacy Ant incremental compiler
can retain obsolete resource IDs after layout changes and crash Settings.

Full background, build-chain gotchas, and the roadmap:
[../docs/06-our-own-app.md](../docs/06-our-own-app.md).
The server that produces the image: [../server](../server).

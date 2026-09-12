# app — NookPanel, our Android 2.1 client

A fullscreen image panel for the Nook Simple Touch: fetch a PNG from a server on
the LAN, draw it, wait, repeat.

Long press the picture or status message to open the Refresh now / Settings menu.
An ordinary tap does not open the menu.

A small battery icon and percentage overlay the top-right corner of the image.
A plus sign indicates charging. The indicator uses the Nook's battery level,
updates only when its displayed state changes, and remains over a retained image
after a failed refresh. Long pressing it opens the same menu.

When an image URL is configured, NookPanel starts automatically after boot,
turns on the display, and dismisses the Nook's slide lock without a button press.

If a refresh fails, the last successfully displayed image stays visible while
the app retries at the configured interval. An error is shown only if no image
has loaded yet. The previous image is held in memory for the current activity;
it is not saved across app restarts.

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

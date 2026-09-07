# app — NookPanel, our Android 2.1 client

A fullscreen image panel for the Nook Simple Touch: fetch a PNG from a server on
the LAN, draw it, wait, repeat.

```bash
make image     # one-time: build the pinned 2014 ADT container
make debug     # -> bin/NookPanel-debug.apk
make install   # adb install -r  (run on the host, Nook plugged in)
```

Full background, build-chain gotchas, and the roadmap:
[../docs/06-our-own-app.md](../docs/06-our-own-app.md).
The server that produces the image: [../server](../server).

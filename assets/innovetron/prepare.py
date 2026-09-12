#!/usr/bin/env python3
"""Convert approved generated artwork to the Nook's existing image formats."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "device"
OUT.mkdir(exist_ok=True)
RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS
ROTATE = getattr(Image, "Transpose", Image).ROTATE_270

for name in ("boot", "sleep", "off"):
    with Image.open(ROOT / "source" / (name + ".png")) as source:
        frame = source.convert("L").resize((600, 800), RESAMPLE)
    frame.convert("RGB").save(OUT / (name + ".png"))
    if name == "boot":
        # The bootloader reads an 800x600 P5 raster rotated clockwise.
        frame.transpose(ROTATE).save(OUT / "booting.pgm")
    if name == "sleep":
        frame.save(OUT / "sleep.jpg", quality=95)

with Image.open(ROOT / "source" / "loading.png") as source:
    source.convert("L").resize((512, 256), RESAMPLE).convert("RGBA").save(
        OUT / "render-0.png"
    )

for name, size, mode in (
    ("booting.pgm", (800, 600), "L"),
    ("render-0.png", (512, 256), "RGBA"),
    ("off.png", (600, 800), "RGB"),
    ("sleep.png", (600, 800), "RGB"),
):
    with Image.open(OUT / name) as result:
        assert result.size == size and result.mode == mode, name
        result.load()
print("Prepared and decoded all Nook artwork formats.")

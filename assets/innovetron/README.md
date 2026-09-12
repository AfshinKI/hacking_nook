# Innovetron Nook screens

Brand reference: https://innovetron.com/ and its
`figures/Innovetron_Logo.png`. The site describes electronics design, FPGA/DSP,
signal integrity and precision PCB design. Artwork uses the orbit/iN logo and
black circuit traces on white for the 600×800 e-ink panel.

Created with the built-in imagegen tool. Original outputs are in `source/`;
`python3 assets/innovetron/prepare.py` converts them to device formats using
Pillow. It only resizes, converts colour modes, and rotates the early splash.

| Device artifact | Destination | Format |
|---|---|---|
| `device/booting.pgm` | `booting.pgm` on mmcblk0p1 | P5, 800×600, clockwise rotation |
| `device/render-0.png` | `/system/assets/boot_images/render-0.png` | RGBA, 512×256 |
| `device/off.png` | `/system/assets/shutdown_images/cold_boot_screen.png` | RGB, 600×800 |
| `device/off.png` | `/system/assets/shutdown_images/autoshutdown_screen.png` | RGB, 600×800 |
| `device/sleep.png` | `/system/media/screensaver/default.png` | RGB, 600×800 |
| `device/sleep.jpg` | Current selected screensaver file (see device notes) | JPEG, 600×800 |

The five existing loading progress frames stay in place. Low-battery, charging,
and factory/recovery images stay in place. `device/boot.png` is an upright preview
of the early boot artwork, not an additional installed file.

## Generation prompts

Boot, referencing `website-logo.png`:

> Create a finished portrait 3:4 e-ink boot screen for INNOVETRON, electronics engineering consultancy specialising in FPGA, DSP and precision PCB design. White background, pure black crisp fine-but-readable technical illustration: elegant printed circuit traces radiate from a central microchip, with the provided actual orbit iN logo accurately inset in the chip. Restrained editorial engineering aesthetic, lots of whitespace, no photorealism, no device mockup, no gradients or shadows. At top exact large text INNOVETRON. Beneath illustration exact text Starting NookPanel. Small footer innovetron.com. Designed to be downsampled to 600x800. Single finished full-page image, no borders outside artwork.

Off, referencing `source/boot.png`:

> Make the matching POWER OFF screen from this boot screen. Preserve exact INNOVETRON wordmark, central chip with orbit iN logo, white background, crisp monochrome circuit illustration and footer innovetron.com. Replace Starting NookPanel. with exact large text Nook is off. Below add small clear text Press the power button to start. Keep clean white space for both lines, scaling illustration slightly if needed. Portrait 3:4 full-page artwork suitable for 600x800 e-ink display, no mockup.

Sleep, referencing `source/boot.png`:

> Make matching SLEEP / LOCK screen from this boot screen. Preserve exact INNOVETRON wordmark, central chip with orbit iN logo, white background and crisp monochrome circuit illustration. Replace Starting NookPanel. with exact text Resting. Keep footer innovetron.com. Place artwork and all text in upper 80 percent, leave bottom 20 percent completely white for the Nook native unlock overlay; move footer above that blank area. Portrait 3:4 full-page artwork suitable for 600x800 e-ink display, no mockup.

Loading, referencing `website-logo.png`:

> Create a matching INNOVETRON loading-logo graphic for an old e-ink boot renderer. Wide 2:1 aspect ratio, will be reduced to 512x256. Pure white background. Center the supplied actual orbit iN logo as a small black rounded square near the upper centre. Beneath it large bold exact text INNOVETRON. Small restrained circuit trace accents left and right of the logo. Clean crisp monochrome, generous white margins, readable at small size, no footer, no other text, no mockup. This is a horizontal companion to an INNOVETRON circuit-board boot splash.

## Device and recovery notes

BNRV300, firmware 1.2.2. Original files and settings are kept locally in the
gitignored `backups/branding-2026-09-12/` directory. The selected screensaver was
`/media/screensavers/Extra/1c77af487780065348f0409fc5841ec7.jpg`; its original is
`selected-screensaver.jpg` in that backup. Replacing this single selected file
keeps the existing screensaver setting and other picture collections intact.

Restore by copying the original files from the backup to their matching
destinations. Mount mmcblk0p1 as VFAT for `booting.pgm`, and temporarily remount
`/system` read-write for the system PNGs. Restore `/system` read-only and unmount
the boot partition after copying. Reboot to reload the cached screensaver.

This changes picture files, not the bootloader, kernel, ramdisk, framework APK,
or partition table. Boot still takes time; the custom images cover those stages.

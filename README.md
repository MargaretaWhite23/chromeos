# ChromeOS technical notes

Operational diagnostics, repairs, and update-persistence checks for the ChromeOS host.

## Documentation

- [Python 3.11 shared-library repair and update persistence](docs/python-3.11-linker-update-persistence.md) — root cause, confirmed repair, ChromeOS A/B partitions, validation and outstanding risks.

- [Tesseract for ChromeOS Fizz](docs/tesseract-chromeos.md) — GitHub Actions build, runtime packaging, and host verification.

## Native VLC on ChromeOS

- [VLC 3.0.24 build](https://github.com/MargaretaWhite23/chromeos/actions/runs/42736588979) compiled the x86_64 musl runtime with stable XDG Shell support, passed the CI transcode test, and published a ZIP and SHA-256 checksum. The staged ZIP also passed its checksum check in Crostini.
- [Wayland diagnostic build](https://github.com/MargaretaWhite23/chromeos/actions/runs/42734589808) ran directly on ChromeOS. The compositor configured a 640 × 480 window and delivered a frame callback. The diagnostic exited with code 0.
- Native VLC video playback on the ChromeOS host still needs verification. The package includes a `vlc-wayland` launcher that uses VLC's dummy interface and Wayland video output.

> No ChromeOS update, reboot, boot-slot change, or automatic startup repair is performed by this repository.

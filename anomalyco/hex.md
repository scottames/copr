# Hex

[![Powered By: Copr](https://img.shields.io/badge/Powered_by-COPR-blue?style=flat-square)](https://copr.fedorainfracloud.org/)
![Architecture: x86_64](https://img.shields.io/badge/Architecture-x86__64-blue?style=flat-square)
![Architecture: aarch64](https://img.shields.io/badge/Architecture-aarch64-blue?style=flat-square)
[![Latest Version](https://img.shields.io/badge/dynamic/json?color=blue&label=Version&query=builds.latest.source_package.version&url=https%3A%2F%2Fcopr.fedorainfracloud.org%2Fapi_3%2Fpackage%3Fownername%3Dscottames%26projectname%3Danomalyco%26packagename%3Dhex%26with_latest_build%3DTrue&style=flat-square&logoColor=blue)](https://copr.fedorainfracloud.org/coprs/scottames/anomalyco/package/hex/)
[![Copr build status](https://copr.fedorainfracloud.org/coprs/scottames/anomalyco/package/hex/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/scottames/anomalyco/package/hex/)

## About

[Hex](https://github.com/anomalyco/hex), a local voice dictation application from
[Anomaly](https://github.com/anomalyco), packaged for Fedora and published to
[COPR](https://copr.fedorainfracloud.org/coprs/scottames/anomalyco/).

This package republishes the official stable upstream RPM with pinned SHA-256
checksums. It does not rebuild Hex from source.

> [!WARNING]
> This COPR is intended for my personal use only.
> Use at your own risk.
> Review the [upstream documentation](https://github.com/anomalyco/hex#readme) first.
> Pull requests and collaboration are welcome!

### Bugs

- **Application bugs**
  - Report to the [Hex repository](https://github.com/anomalyco/hex/issues).
- **Packaging bugs**
  - Report to [this GitHub project](https://github.com/scottames/copr/issues).

## Installation

```bash
sudo dnf copr enable scottames/anomalyco
sudo dnf install hex
```

## Updating

```bash
sudo dnf upgrade hex
```

## Notes

Hex downloads a speech model on first use. Launch Hex from the application menu
to configure dictation. Its upstream systemd user unit is included but is not
enabled by this package.

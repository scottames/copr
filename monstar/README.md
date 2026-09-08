# monstar

[![Powered By: Copr](https://img.shields.io/badge/Powered_by-COPR-blue?style=flat-square)](https://copr.fedorainfracloud.org/)
![Architectures: x86_64, aarch64](https://img.shields.io/badge/Architectures-x86__64%2C_aarch64-blue?style=flat-square)
[![Latest Version](https://img.shields.io/badge/dynamic/json?color=blue&label=Version&query=builds.latest.source_package.version&url=https%3A%2F%2Fcopr.fedorainfracloud.org%2Fapi_3%2Fpackage%3Fownername%3Dscottames%26projectname%3Dmonstar%26packagename%3Dmonstar%26with_latest_build%3DTrue&style=flat-square&logoColor=blue)](https://copr.fedorainfracloud.org/coprs/scottames/monstar/package/monstar/)
[![Copr build status](https://copr.fedorainfracloud.org/coprs/scottames/monstar/package/monstar/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/scottames/monstar/package/monstar/)

## About

[Monstar](https://github.com/rockorager/monstar) is a Linux-native Wayland
terminal built on the Ghostty terminal core. This package builds Monstar from
the source archive attached to its GitHub releases and publishes it to
[Copr](https://copr.fedorainfracloud.org/coprs/scottames/monstar).

>[!WARNING]
> This Copr is intended for my personal use only. Use at your own risk.
>
> The upstream source archive does not vendor its Zig dependencies, so the Copr
> project must allow network access during builds.

### Bugs

- Application bugs should be reported to the
  [Monstar GitHub repository](https://github.com/rockorager/monstar/issues).
- Packaging bugs should be reported to
  [this GitHub project](https://github.com/scottames/copr/issues).

## Installation

1. Enable the Copr repository:

```bash
sudo dnf copr enable scottames/monstar
```

2. Install Monstar:

```bash
sudo dnf install monstar
```

## Updating

```bash
sudo dnf upgrade monstar
```

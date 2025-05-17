# Ghostty

[![⚡️Powered By: Copr](https://img.shields.io/badge/⚡️_Powered_by-COPR-blue?style=flat-square)](https://copr.fedorainfracloud.org/)
![📦 Architecture: x86_64](https://img.shields.io/badge/📦_Architecture-x86__64-blue?style=flat-square)
[![Latest Version](https://img.shields.io/badge/dynamic/json?color=blue&label=Version&query=builds.latest.source_package.version&url=https%3A%2F%2Fcopr.fedorainfracloud.org%2Fapi_3%2Fpackage%3Fownername%3Dscottames%26projectname%3Dghostty%26packagename%3Dghostty%26with_latest_build%3DTrue&style=flat-square&logoColor=blue)](https://copr.fedorainfracloud.org/coprs/scottames/ghostty/package/ghostty/)
[![Copr build status](https://copr.fedorainfracloud.org/coprs/scottames/ghostty/package/ghostty/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/scottames/ghostty/package/ghostty/)

## About

[Ghostty](https://ghostty.org) packaged for Fedora and published to [copr](https://copr.fedorainfracloud.org/coprs/scottames/ghostty)

### Bugs

- Bugs related to Ghostty application should be reported to the [ghostty-org GitHub org](https://github.com/ghostty-org/ghostty/issues)
- Bugs related to this package should be reported to [this Git project](https://github.com/scottames/copr/issues)

## Installation

1. Enable copr repo

```bash
sudo dnf copr enable scottames/ghostty
```

  - Substitute `dnf` for `yum` if desired

2. (Optional) Update package list

```bash
sudo dnf check-update
```

3. Install

```bash
sudo dnf install ghostty
```

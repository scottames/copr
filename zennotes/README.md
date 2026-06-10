# zennotes

[![Powered By: Copr](https://img.shields.io/badge/Powered_by-COPR-blue?style=flat-square)](https://copr.fedorainfracloud.org/)
![Architecture: x86_64](https://img.shields.io/badge/Architecture-x86__64-blue?style=flat-square)
[![Latest Version](https://img.shields.io/badge/dynamic/json?color=blue&label=Version&query=builds.latest.source_package.version&url=https%3A%2F%2Fcopr.fedorainfracloud.org%2Fapi_3%2Fpackage%3Fownername%3Dscottames%26projectname%3Dzennotes%26packagename%3Dzennotes%26with_latest_build%3DTrue&style=flat-square&logoColor=blue)](https://copr.fedorainfracloud.org/coprs/scottames/zennotes/package/zennotes/)
[![Copr build status](https://copr.fedorainfracloud.org/coprs/scottames/zennotes/package/zennotes/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/scottames/zennotes/package/zennotes/)

## About

[ZenNotes](https://github.com/ZenNotes/zennotes) packaged for Fedora and
published to [copr](https://copr.fedorainfracloud.org/coprs/scottames/zennotes).

This package republishes the official upstream GitHub Release DEB so Fedora can
install and update ZenNotes through normal DNF/COPR metadata.

>[!WARNING]
> This copr is intended for my personal use only.
> Use at your own risk.
>
> - This package uses upstream's prebuilt Electron DEB; it does not rebuild
>   ZenNotes from source.
> - Updates should be installed through DNF/COPR, not the app's upstream
>   self-updater.
>
> Given that, pull requests and collaboration are welcome!

### Bugs

- Bugs related to the ZenNotes application should be reported to the
  [ZenNotes GitHub repo](https://github.com/ZenNotes/zennotes/issues).
- Bugs related to this package should be reported to
  [this GitHub project](https://github.com/scottames/copr/issues).

## Installation

1. Enable copr repo

```bash
sudo dnf copr enable scottames/zennotes
```

- Substitute `dnf` for `yum` if desired.

2. (Optional) Update package list

```bash
sudo dnf check-update
```

3. Install

```bash
sudo dnf install zennotes
```

## Updating

```bash
sudo dnf upgrade zennotes
```

## Notes

- Fedora builds are x86_64 only for now, matching upstream's Linux DEB asset.
- The package provides `zennotes` for the desktop app and `zen` for the bundled
  ZenNotes CLI wrapper.

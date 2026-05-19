# voxtype

[![Powered By: Copr](https://img.shields.io/badge/Powered_by-COPR-blue?style=flat-square)](https://copr.fedorainfracloud.org/)
![Architecture: x86_64](https://img.shields.io/badge/Architecture-x86__64-blue?style=flat-square)
[![Latest Version](https://img.shields.io/badge/dynamic/json?color=blue&label=Version&query=builds.latest.source_package.version&url=https%3A%2F%2Fcopr.fedorainfracloud.org%2Fapi_3%2Fpackage%3Fownername%3Dscottames%26projectname%3Dvoxtype%26packagename%3Dvoxtype%26with_latest_build%3DTrue&style=flat-square&logoColor=blue)](https://copr.fedorainfracloud.org/coprs/scottames/voxtype/package/voxtype/)
[![Copr build status](https://copr.fedorainfracloud.org/coprs/scottames/voxtype/package/voxtype/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/scottames/voxtype/package/voxtype/)

## About

[Voxtype](https://github.com/peteonrails/voxtype) packaged for Fedora and
published to [copr](https://copr.fedorainfracloud.org/coprs/scottames/voxtype).

This package republishes the official upstream GitHub Release RPM so Fedora can
install and update Voxtype through normal DNF/COPR metadata.

>[!WARNING]
> This copr is intended for my personal use only.
> Use at your own risk.
>
> - It is highly recommended to review the
>   [official install documentation](https://github.com/peteonrails/voxtype/blob/dev/docs/INSTALL.md)
>   first.
> - This package uses upstream's prebuilt binary RPM; it does not rebuild
>   Voxtype from source.
>
> Given that, pull requests and collaboration are welcome!

### Bugs

- Bugs related to the Voxtype application should be reported to the
  [Voxtype GitHub repo](https://github.com/peteonrails/voxtype).
- Bugs related to this package should be reported to
  [this GitHub project](https://github.com/scottames/copr/issues).

## Installation

1. Enable copr repo

```bash
sudo dnf copr enable scottames/voxtype
```

- Substitute `dnf` for `yum` if desired.

1. (Optional) Update package list

```bash
sudo dnf check-update
```

1. Install

```bash
sudo dnf install voxtype
```

## Updating

```bash
sudo dnf upgrade voxtype
```

## Notes

- Fedora builds are x86_64 only for now, matching upstream's packaged RPM.
- Upstream publishes experimental aarch64 binaries, but the 0.7.2 RPM package
  path is x86_64-only.
- Recommended optional runtime tools include `wtype`, `wl-clipboard`,
  `libnotify`, `playerctl`, `dotool`, and `vulkan-loader`, depending on your
  compositor and acceleration path.

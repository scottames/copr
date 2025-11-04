# vicinae

[![⚡️Powered By: Copr](https://img.shields.io/badge/⚡️_Powered_by-COPR-blue?style=flat-square)](https://copr.fedorainfracloud.org/)
![📦 Architecture: x86_64](https://img.shields.io/badge/📦_Architecture-x86__64-blue?style=flat-square)
[![Latest Version](https://img.shields.io/badge/dynamic/json?color=blue&label=Version&query=builds.latest.source_package.version&url=https%3A%2F%2Fcopr.fedorainfracloud.org%2Fapi_3%2Fpackage%3Fownername%3Dscottames%26projectname%3Dvicinae%26packagename%3Dvicinae%26with_latest_build%3DTrue&style=flat-square&logoColor=blue)](https://copr.fedorainfracloud.org/coprs/scottames/vicinae/package/vicinae/)
[![Copr build status](https://copr.fedorainfracloud.org/coprs/scottames/vicinae/package/vicinae/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/scottames/vicinae/package/vicinae/)

## About

[vicinae](https://github.com/vicinaehq/vicinae) packaged for Fedora and
published to [copr](https://copr.fedorainfracloud.org/coprs/scottames/vicinae)

>[!WARNING]
> This copr is intended for my personal use only.
> Use at your own risk.
> Given that, pull requests and collaboration are welcome!

### Bugs

- Bugs related to the vicinae application should be reported to the
  [vicinae GitHub repo](https://github.com/vicinaehq/vicinae)
- Bugs related to this package should be reported to [this GitHub project](https://github.com/scottames/copr/issues)

## Installation

1. Enable copr repo

```bash
sudo dnf copr enable scottames/vicinae
```

- Substitute `dnf` for `yum` if desired

1. (Optional) Update package list

```bash
sudo dnf check-update
```

1. Install

```bash
sudo dnf install vicinae
```

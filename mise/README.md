# mise

[![⚡️Powered By: Copr](https://img.shields.io/badge/⚡️_Powered_by-COPR-blue?style=flat-square)](https://copr.fedorainfracloud.org/)
![📦 Architecture: x86_64](https://img.shields.io/badge/📦_Architecture-x86__64-blue?style=flat-square)
[![Latest Version](https://img.shields.io/badge/dynamic/json?color=blue&label=Version&query=builds.latest.source_package.version&url=https%3A%2F%2Fcopr.fedorainfracloud.org%2Fapi_3%2Fpackage%3Fownername%3Dscottames%26projectname%3Dmise%26packagename%3Dmise%26with_latest_build%3DTrue&style=flat-square&logoColor=blue)](https://copr.fedorainfracloud.org/coprs/scottames/mise/package/mise/)
[![Copr build status](https://copr.fedorainfracloud.org/coprs/scottames/mise/package/mise/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/scottames/mise/package/mise/)

## About

[mise](https://github.com/jdx/mise) packaged for Fedora and published to
[copr](https://copr.fedorainfracloud.org/coprs/scottames/mise)

>[!WARNING]
> This copr is intended for my personal use only.
> Use at your own risk.
>
> - It is highly recommended to use the [official install](https://mise.jdx.dev)
>   instead.
>
> Given that, pull requests and collaboration are welcome!

### Bugs

- Bugs related to the mise application should be reported to the
  [mise GitHub repo](https://github.com/jdx/mise)
- Bugs related to this package should be reported to
  [this GitHub project](https://github.com/scottames/copr/issues)

## Installation

1. Enable copr repo

```bash
sudo dnf copr enable scottames/mise
```

- Substitute `dnf` for `yum` if desired

1. (Optional) Update package list

```bash
sudo dnf check-update
```

1. Install

```bash
sudo dnf install mise
```

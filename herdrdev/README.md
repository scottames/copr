# herdrdev

[![Powered By: Copr](https://img.shields.io/badge/Powered_by-COPR-blue?style=flat-square)](https://copr.fedorainfracloud.org/)
![Architectures: x86_64, aarch64](https://img.shields.io/badge/Architectures-x86__64%2C_aarch64-blue?style=flat-square)
[![herdr-app build status](https://copr.fedorainfracloud.org/coprs/scottames/herdrdev/package/herdr-app/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/scottames/herdrdev/package/herdr-app/)
[![herdr-core build status](https://copr.fedorainfracloud.org/coprs/scottames/herdrdev/package/herdr-core/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/scottames/herdrdev/package/herdr-core/)

## About

[Herdr](https://github.com/herdrdev/herdr-app) is a desktop app for terminals and
coding agents. Its separate [herdr-core](https://github.com/herdrdev/herdr-core)
runtime keeps terminals running when the window closes.

Both packages republish upstream's prebuilt Linux binaries through
[Copr](https://copr.fedorainfracloud.org/coprs/scottames/herdrdev). They do not
build from source or run upstream's installation scripts.

>[!WARNING]
> This Copr is intended for my personal use only. Use at your own risk.
>
> Review upstream's [security and privacy documentation](https://github.com/herdrdev/herdr-app/blob/master/docs/security.md).
> Mods run with your account's access, and app telemetry is enabled by default.
> Disable telemetry in Settings → Privacy if desired.

### Bugs

- Application bugs should be reported to the relevant upstream repository:
  - [herdr-app](https://github.com/herdrdev/herdr-app/issues)
  - [herdr-core](https://github.com/herdrdev/herdr-core/issues)
- Packaging bugs should be reported to
  [this GitHub project](https://github.com/scottames/copr/issues).

## Installation

1. Enable the Copr repository:

```bash
sudo dnf copr enable scottames/herdrdev
```

2. Install the desktop app and its core dependency:

```bash
sudo dnf install herdr-app
```

For a CLI-only machine, install `herdr-core` instead. It provides both
`herdr-core` and the `hc` shortcut. Run either package as your regular user,
not root. The core starts on demand; no service needs to be enabled manually.

## Updating

```bash
sudo dnf upgrade herdr-app herdr-core
```

The RPM layout disables the app's self-updater. The core also leaves its
system-installed binary to the package manager. Use DNF, not `hc update`.
After upgrading, quit and reopen the app and restart your running core as your
regular user:

```bash
herdr-core server restart
```

The planned core restart keeps terminal programs running.

## Notes

- Linux needs a desktop session and a working Vulkan driver for the app.
- Older script or mise installs can take precedence over `/usr/bin`.
  - Check `command -v herdr-app` and `command -v herdr-core` when switching.
  - The app's `core` setting can select `/usr/bin/herdr-core` explicitly.
- These packages are separate from the older `herdr` terminal application.

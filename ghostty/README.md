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

## Known Issues

### Parallels and Older OpenGL Environments

Ghostty requires OpenGL 4.3. Some virtualized or older graphics environments,
including Fedora guests running under Parallels Desktop on macOS, may expose only
OpenGL 4.0 or 4.1. In that case, Ghostty may fail to start with messages like:

```text
warning(opengl): OpenGL version is too old. Ghostty requires OpenGL 4.3
warning(gtk_ghostty_surface): failed to initialize surface err=error.OpenGLOutdated
```

As a workaround, run Ghostty with Mesa software rendering enabled:

```bash
LIBGL_ALWAYS_SOFTWARE=true ghostty
```

To apply this workaround to a per-user desktop launcher, copy the packaged
desktop file and update the `Exec=` line:

```bash
mkdir -p ~/.local/share/applications
cp /usr/share/applications/com.mitchellh.ghostty.desktop ~/.local/share/applications/
```

Change:

```desktop
Exec=/usr/bin/ghostty --gtk-single-instance=true
```

to:

```desktop
Exec=env LIBGL_ALWAYS_SOFTWARE=true /usr/bin/ghostty --gtk-single-instance=true
```

Software rendering can be slower and should only be used on systems where the
normal GPU-backed launch path fails.

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

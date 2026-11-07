# Hokum

This package republishes the official stable Hokum RPM with pinned SHA-256
checksums. It supports x86_64 and aarch64 on the repository's default Fedora
targets. Renovate groups both architectures' version and checksum updates.

```sh
sudo dnf copr enable scottames/anomalyco
sudo dnf install hokum
```

Hokum requires a Wayland compositor with layer-shell support. It starts through
D-Bus activation; to start it with the graphical session instead:

```sh
systemctl --user enable --now hokum.service
```

Only one notification daemon can own `org.freedesktop.Notifications`. Stop or
disable any existing notification daemon before starting Hokum.

## COPR package setup

Before merging, create the `hokum` package in `scottames/anomalyco` with:

- Source type: Git SCM
- Clone URL: `https://github.com/scottames/copr.git`
- Committish: `main`
- Subdirectory: `anomalyco`
- Spec file: `hokum.spec`
- Build SRPM with: `rpkg`

The existing merge workflow calls `copr-cli build-package` for this package.
It does not create the package definition. The project must enable the default
Fedora targets for both x86_64 and aarch64.

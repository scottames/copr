# Hex

This package republishes the official stable Hex RPM with pinned SHA-256
checksums. It supports x86_64 and aarch64 on the repository's default Fedora
targets. Renovate groups both architectures' version and checksum updates.

```sh
sudo dnf copr enable scottames/anomalyco
sudo dnf install hex
```

Hex downloads a speech model on first use. Launch Hex from the application menu
to configure dictation. Its upstream systemd user unit is included but is not
enabled by this package.

## COPR package setup

Before merging, create the `hex` package in `scottames/anomalyco` with:

- Source type: Git SCM
- Clone URL: `https://github.com/scottames/copr.git`
- Committish: `main`
- Subdirectory: `anomalyco`
- Spec file: `hex.spec`
- Build SRPM with: `rpkg`

The existing merge workflow calls `copr-cli build-package` for this package.
It does not create the package definition. The project must enable the default
Fedora targets for both x86_64 and aarch64.

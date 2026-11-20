# xremap for Fedora x86_64

This package builds one `xremap` binary. It installs no units, device rules,
users, groups or mappings. Deployment and rollback testing belong to SCT-376.

## Build inputs

- `git ls-remote https://github.com/xremap/xremap.git refs/tags/v0.15.18`
  returned `23e880d441bf968de396c731fdcea18b1af62d9b`. The spec fetches the
  archive by that commit and checks its SHA-256 before extraction.
- Starting from the archive's lockfile, `cargo update -p rustix@1.1.5 --precise
  1.1.6` changed only the rustix version and registry checksum. Both lockfile
  hashes are enforced in `%prep`. Do not regenerate the lock during a build.
- Cargo and rustc are pinned to 1.99.1 on Fedora 44 and 1.100.0 on Fedora 45.
  The Fedora chroot supplies the C
  linker and RPM tooling. Keep the COPR buildroot package list with each
  build; OS updates can change the resulting RPM hash.
- Cargo fetches crates over the network and verifies registry checksums from
  the lockfile. Build and tests use `--release --locked --no-default-features
  --features socket,niri`. The upstream `full` and `device-test` features are
  intentionally excluded.

## Dependency review (2026-11-19)

From the unpacked source with the packaged `Cargo.lock`, the release graph is:

```sh
cargo tree --locked --target x86_64-unknown-linux-gnu --no-default-features \
  --features socket,niri -e normal,build --prefix none --format '{p}'
```

An OSV `v1/querybatch` check of all 118 distinct crates.io name/version pairs
from this tree returned four findings. Recheck the selected graph before each
promotion; the lock also contains optional crates that do not ship.

| Build dependency | Trial decision and follow-up |
| --- | --- |
| rustix 1.1.6 | Fixes RUSTSEC-2026-0486; no OSV hit for the selected version. |
| serde_yaml 0.9.34+deprecated → unsafe-libyaml 0.2.11 | RUSTSEC-2024-0449: temporarily retain the unmaintained parser. Use TOML in deployment; it does not remove the compiled dependency. Revisit when upstream replaces or gates YAML. |
| zbus 5.19.0 → zbus_names 4.3.5, zvariant 5.15.1, zvariant_derive 5.15.1 | RUSTSEC-2026-0371, -0370 and -0372: temporarily retain these unmaintained crates for `socket`. Upstream requires zbus `^5.15.0`; migration to 6 requires source review and service/bridge testing, not a lock-only update. Revisit at the next upstream bump. |

The local x86_64 release build reported `xremap 0.15.18`; 374 tests passed.
Its **standalone binary** SHA-256 was
`f8052c49c298c1066bf1681adf89dcd2fc9fff8fd7bb8e160b144b2b7b813889`.
These checks do not exercise physical input devices or a live Niri session.

## COPR handoff (Scotty)

After the reviewed spec and lock are available together on `main`, create the
project and its SCM package once, then request the build:

```sh
copr-cli create --chroot fedora-44-x86_64 --chroot fedora-45-x86_64 \
  --enable-net on scottames/xremap
copr-cli add-package-scm scottames/xremap --name xremap --type git \
  --clone-url https://github.com/scottames/copr.git --commit main \
  --subdir xremap --spec xremap.spec --method rpkg --webhook-rebuild off
copr-cli build-package --chroot fedora-44-x86_64 --chroot fedora-45-x86_64 \
  --name xremap scottames/xremap
```

If the repository workflow has already requested the build, inspect that build
instead of submitting another. Before promotion, record the COPR build ID,
packaging commit, chroots and `sha256sum` of each downloaded RPM and SRPM in
SCT-382. Retain the previous tested RPM and its checksum for rollback.

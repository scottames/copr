# xremap package maintenance

## Build inputs

The spec pins v0.15.18 to commit
`23e880d441bf968de396c731fdcea18b1af62d9b` and verifies the source archive,
upstream lockfile, and replacement lockfile hashes. The only lockfile change
updates rustix 1.1.5 to 1.1.6 and its checksum.

Cargo and rustc are both pinned to `1.100.0`. Before changing the pins, check
availability in the enabled Fedora repositories on both x86_64 and aarch64.
Exact pins can stop resolving when Fedora updates replace repository packages.
Retain buildroot package lists and artifact checksums because OS tooling can
also affect the output.

Build and test with `--release --locked --no-default-features --features full`.
`device-test` is excluded. COPR networking must be enabled to fetch locked
crates. Default PR build targets are selected by the shared
`.github/spec-build-targets.json`.

## Dependency review

The reviewed lockfile has these accepted unmaintained-crate exceptions:

| Crate | Version | Advisory |
| --- | --- | --- |
| unsafe-libyaml | 0.2.11 | RUSTSEC-2024-0449 |
| zbus_names | 4.3.5 | RUSTSEC-2026-0371 |
| zvariant | 5.15.1 | RUSTSEC-2026-0370 |
| zvariant_derive | 5.15.1 | RUSTSEC-2026-0372 |

These exceptions retain upstream YAML and zbus 5 support. Revisit YAML when
the parser is replaced or gated, and zbus at the next upstream update.
A zbus 6 migration needs source and service testing.

rustix 1.1.6 addresses RUSTSEC-2026-0486. Using TOML does not remove the
compiled YAML dependency. Recheck advisories before promotion against each
target's normal/build dependency graph:

```sh
cargo tree --locked --target TARGET-unknown-linux-gnu \
  --no-default-features --features full -e normal,build
```

Replace `TARGET` with `x86_64` or `aarch64`. Record the dependency graph,
audit date, findings, and exception decisions with the release review.

## Tests

The spec's `%check` runs non-device Rust tests, desktop-feature assertions,
and valid/invalid configuration checks as part of every normal RPM build.

PR CI has separate build and package-lifecycle steps. The shared Dagger
`test-package` function reuses the build graph, then explicitly runs
`test-package.sh`. Cached build steps are reused when available; a cold
cache can require another build.

From the repository root:

```sh
dagger call build-spec-file \
  --spec-file xremap/xremap.spec --fedora-version FEDORA_VERSION
dagger call test-package \
  --spec-file xremap/xremap.spec --fedora-version FEDORA_VERSION \
  --test-script xremap/test-package.sh --package-name xremap
```

Replace `FEDORA_VERSION` with a configured build target. Run each supported
architecture on its matching runner; the container uses the runner's native
architecture.

The lifecycle script checks installation, account creation, unit/rule syntax,
ownership, disabled defaults, state preservation on reinstall, and removal.
**Run it only in a disposable Fedora container:** it writes `/etc` and removes
the RPM. Dagger supplies `PACKAGE_TEST_DISPOSABLE=1`; direct container runs
must set this flag and run as root. It never starts a remapper.

These checks do not replace live device, desktop, SELinux, or service-upgrade
testing.

## Upstream references and Fedora adaptations

These links are pinned to the packaged commit, not the moving upstream branch.
Recheck them when updating the source. The local `README.md` is installed as
`README.fedora`, alongside this maintenance guide. Upstream's README,
documentation, and example mappings are installed separately without local
edits.

| Local file | Upstream reference | Fedora adaptation |
| --- | --- | --- |
| `xremap.spec` | [Feature definitions][upstream-features], [source builds][upstream-build], [release workflow][upstream-ci] | RPM layout, toolchain pins, verified inputs, targets, and lifecycle macros. Completions come from the [upstream binary][upstream-cli-source]. |
| `Cargo.lock` | [Upstream lockfile][upstream-lock] | Only the reviewed rustix update differs. Provenance stays outside this generated file to preserve its hash. |
| `xremap.service` | [System-service example][upstream-system-unit] | Multi-user target, ordering, config guard, quiet logs, delayed failure restart, and root-owned configuration. Per-user socket setup remains explicit. |
| `xremap-user.service` | [Example unit][upstream-user-unit], [user-service guide][upstream-user] | Graphical-session lifecycle, mode conflict, config guard, quiet logs, and delayed failure restart. The example's memory/network limits are not copied. |
| `xremap-bridge.service` | [Bridge command and guidance][upstream-bridge] | Fedora-authored wrapper; upstream supplies no separate bridge unit in this release. Adds session lifecycle, mode conflict, quiet logs, and recovery. |
| `xremap-sysusers.conf` | [Service-account creation][upstream-account], [sysusers.d][sysusers] | Declarative non-login account; no home directory is created. The unit supplies `input` membership instead of changing `/etc/group`. |
| `xremap-modules.conf` | [uinput module setup][upstream-module] | Vendor configuration under `/usr/lib/modules-load.d`, not administrator configuration under `/etc`. |
| `70-xremap.rules` | [uinput permissions][upstream-uinput] | Uses group `xremap`, not `input`, and omits the desktop-session `uaccess` grant. |
| `80-xremap.preset` | [Manual activation][upstream-enable], [systemd presets][presets] | Fedora-authored opt-in activation policy, not an upstream-supplied file. |
| `test-package.sh` | [CLI contracts][upstream-cli], [service setup][upstream-system] | Fedora-authored RPM checks, not upstream hardware tests. |
| `README.md` | Upstream guides | User guide, installed as `README.fedora`. |
| `MAINTENANCE.md` | This table | Package-maintenance guide. |

The Dagger and PR-workflow changes are repository-owned build infrastructure,
not upstream installation files.

## COPR builds

Use the existing `scottames/xremap` project. Check its configured SCM source
and enabled chroots, and check for an existing build before requesting another:

```sh
copr-cli build-package --name xremap scottames/xremap
```

This builds the enabled project chroots. Use explicit `--chroot` options to
limit a build when needed. Record build IDs, packaging commit, chroots,
RPM/SRPM SHA-256 checksums, and dependency findings with the release review.

[upstream-features]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/Cargo.toml
[upstream-build]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/doc/development/install_from_source.md
[upstream-ci]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/.github/workflows/build.yml
[upstream-cli-source]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/src/main_impl.rs
[upstream-lock]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/Cargo.lock
[upstream-system]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/doc/running_as_system_service.md
[upstream-system-unit]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/doc/running_as_system_service.md#create-service-file
[upstream-user]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/doc/running_as_user_service.md
[upstream-user-unit]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/example/xremap.service
[upstream-bridge]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/doc/running_as_system_service.md#other-desktops-than-gnome
[upstream-account]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/doc/running_as_system_service.md#create-a-system-user-named-xremap
[upstream-module]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/doc/running_without_sudo.md#module-to-output-artificial-events
[upstream-uinput]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/doc/running_without_sudo.md#output-permission
[upstream-enable]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/doc/running_as_system_service.md#autostart-xremap-at-boot
[upstream-cli]: https://github.com/xremap/xremap/blob/23e880d441bf968de396c731fdcea18b1af62d9b/README.md#commandline-arguments
[sysusers]: https://www.freedesktop.org/software/systemd/man/latest/sysusers.d.html
[presets]: https://www.freedesktop.org/software/systemd/man/latest/systemd.preset.html

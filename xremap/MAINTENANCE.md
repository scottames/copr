# xremap package maintenance

## Build inputs

`xremap.spec` is the source of truth for the package version, source commit,
compiler requirement, and build features. Source downloads use the pinned commit.
We trust GitHub HTTPS to serve that revision; there is no separate archive
checksum to refresh.

Cargo and rustc use the spec's exact compiler requirement. Before changing it,
check availability in the enabled Fedora repositories on both x86_64 and
aarch64. Exact pins can stop resolving when Fedora replaces repository packages.
Retain buildroot package lists and artifact checksums because OS tooling can
also affect the output.

The spec builds upstream's `full` variant with locked dependencies and excludes
`device-test`. COPR networking must be enabled to fetch locked crates. Default
PR build targets are selected by the shared `.github/spec-build-targets.json`.

## Updating the package

Renovate updates the version and commit together and resets `Release`.
Digest-only retag updates are disabled. Normal repository automerge applies
when checks pass; no maintainer command is needed for a routine update.

An expired temporary patch guard still needs a real packaging decision. If
upstream includes the fix, remove it with the repository's existing helper:

```sh
scripts/fix-spec-guards.sh --apply xremap/xremap.spec
```

If a fix is still needed, port and explicitly review the patch for the new
release; do not merely extend its guard. Add temporary patches with
`scripts/add-temporary-spec-patch.sh`. Use upstream's lockfile, not a complete
downstream replacement. Keep dependency corrections as small guarded patches.

CI checks that the source version matches the spec, builds each target,
validates installed documentation paths, and audits the patched lockfile.
Investigate failed checks rather than manually preparing every release.
The historical provenance baseline below is separate from the current package
version; update it only when revising the adaptations.

## Dependency review

CI uses standard `cargo audit`, not a custom audit client. It checks out the
pinned upstream commit, applies downstream patches, and audits the entire
lockfile, including dev and optional dependencies. The separate yank check is
disabled; locked RPM builds check dependency availability and buildability.

`.cargo/audit.toml` records the accepted unmaintained-crate advisory IDs.
CI denies other findings and warnings. Unlike the previous version-specific
exceptions, these acknowledgements cover the advisory across affected crate
versions. New advisory IDs still fail; unused acknowledgements do not.
Remove obsolete entries during normal maintenance, not as a condition for
an otherwise healthy upgrade.

In the prepared upstream source directory, after applying downstream patches,
review the target graphs when deciding whether a finding applies:

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

The service/device adaptations were reviewed against this immutable
[upstream source tree][provenance]. Paths below are relative to that historical
baseline, not claims about the currently packaged release.

The local `README.md` is installed as `README.fedora`, alongside this maintenance
guide. Upstream's README, documentation, and example mappings are installed
without local edits and match the installed binary. Unit `Documentation=`
entries point at those local files. README web links follow latest upstream
documentation and are labelled accordingly.

| Local file | Upstream reference | Fedora adaptation |
| --- | --- | --- |
| `xremap.spec` | [`Cargo.toml`, `doc/development/install_from_source.md`, `.github/workflows/build.yml`, `src/main_impl.rs`][provenance] | RPM layout, build controls, completions, and lifecycle macros. |
| Guarded lockfile patches | [`Cargo.lock`][provenance]; advisory links in each patch | Temporary dependency corrections without freezing upstream's dependency graph. |
| `xremap.service` | [`doc/running_as_system_service.md`][provenance] | Multi-user target, ordering, config guard, quiet logs, delayed failure restart, and root-owned configuration. Per-user socket setup remains explicit. |
| `xremap-user.service` | [`example/xremap.service`, `doc/running_as_user_service.md`][provenance] | Graphical-session lifecycle, mode conflict, config guard, quiet logs, and delayed failure restart. The example's memory/network limits are not copied. |
| `xremap-bridge.service` | Bridge guidance in [`doc/running_as_system_service.md`][provenance] | Fedora-authored wrapper; the baseline supplies no separate bridge unit. Adds session lifecycle, mode conflict, quiet logs, and recovery. |
| `xremap-sysusers.conf` | Account setup in `doc/running_as_system_service.md`; [sysusers.d][sysusers] | Declarative non-login account; no home directory is created. The unit supplies `input` membership instead of changing `/etc/group`. |
| `xremap-modules.conf` | [`doc/running_without_sudo.md`][provenance] | Vendor configuration under `/usr/lib/modules-load.d`, not administrator configuration under `/etc`. |
| `70-xremap.rules` | [`doc/running_without_sudo.md`][provenance] | Uses group `xremap`, not `input`, and omits the desktop-session `uaccess` grant. |
| `80-xremap.preset` | Manual activation in `doc/running_as_system_service.md`; [systemd presets][presets] | Fedora-authored opt-in activation policy, not an upstream-supplied file. |
| `test-package.sh` | [`README.md`, `doc/running_as_system_service.md`][provenance] | Fedora-authored RPM checks, not upstream hardware tests. |
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

[provenance]: https://github.com/xremap/xremap/tree/23e880d441bf968de396c731fdcea18b1af62d9b
[sysusers]: https://www.freedesktop.org/software/systemd/man/latest/sysusers.d.html
[presets]: https://www.freedesktop.org/software/systemd/man/latest/systemd.preset.html

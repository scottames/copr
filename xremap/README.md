# xremap for Fedora

A general-purpose xremap package for Fedora 44 and 45 on x86_64 and aarch64,
built with upstream's `full` desktop support.

The RPM includes optional system and user services, device setup, shell
completions, upstream documentation, and examples. **Services are disabled on
installation. No active mappings or desktop-user permission grants are installed.**

## Install

```sh
sudo dnf copr enable scottames/xremap
sudo dnf install xremap
```

On an Atomic Desktop, add the COPR repository to the host or image, install
through the normal image/layering workflow, and reboot.

The RPM creates a non-login `xremap` account and configures uinput module loading
and device access. These device settings apply even while services are disabled.
Reboot to apply them, or follow upstream's [without-reboot instructions][setup-reboot].

## Configure xremap

Use upstream's [configuration reference][setup-config], [CLI reference][setup-cli],
and [troubleshooting guide][setup-troubleshooting]. Choose a startup mode:

| Mode | Upstream guide | Packaged units | Default configuration |
| --- | --- | --- | --- |
| System service with desktop bridge — recommended | [System-service setup][setup-system] | System `xremap.service`; user `xremap-bridge.service` | `/etc/xremap/config.yml` |
| Direct user service | [User-service setup][setup-user] and [device permissions][setup-permissions] | User `xremap.service` | `~/.config/xremap/config.yml` |

These guides match the packaged release. Apply the RPM-specific differences
below rather than repeating upstream's manual installation steps.

### What the RPM already supplies

For system-service mode, skip upstream's account, configuration-directory,
service-file, uinput-rule, and module-file creation steps. The RPM supplies
those components, but not your mappings or per-user socket groups. Direct
user mode still needs the additional device grants described below.

Do not copy upstream units over the packaged units. Use
`sudo systemctl edit xremap.service` for system overrides or
`systemctl --user edit UNIT` as the desktop user for user overrides.

The Fedora system service expects a **root-owned** configuration, unlike
upstream's service-owned example. After validating your mappings, install them
with `sudo install -o root -g root -m 0644 ./config.yml /etc/xremap/config.yml`.
Examples and upstream documentation are also installed in `/usr/share/doc/xremap/`.

For TOML or other command options, replace `ExecStart` in a drop-in; clear the
old value with `ExecStart=` first. Use `systemctl cat xremap.service` or
`systemctl --user cat UNIT` to see the shipped command instead of copying a
second command template from this README.

### Device and socket permissions

The system unit supplies `input` membership only to its service process. Our
uinput rule grants access to group `xremap`, **not** to `input` or the active
desktop user as in upstream's direct-user example. Direct user mode therefore
needs a local rule or ACL. Do not add desktop users to the service's `xremap`
group.

For bridge mode, follow upstream's [per-user group setup][setup-groups].
Add the corresponding socket-directory entries through a system-service
drop-in rather than editing the vendor unit. This packaging-specific example
uses `+` so directory creation runs as root while the remapper stays unprivileged:

```systemd
[Service]
SupplementaryGroups=SOCKET_GROUP
ExecStartPre=+/usr/bin/install -d -o xremap -g SOCKET_GROUP -m 2770 /run/xremap/UID
```

Replace `SOCKET_GROUP` and `UID` for each intended user. Follow upstream for
group membership, session refresh, and socket-access restrictions.

### Activation and session integration

After completing the chosen setup, enable only its units. For bridge mode:

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now xremap.service
systemctl --user enable --now xremap-bridge.service
```

If the system service is already running, restart it after changing socket
setup. For direct user mode, use `systemctl --user enable --now xremap.service`
instead. Do not run both remappers against the same devices: the user units
conflict, but systemd cannot enforce conflicts across system and user managers.

Our user units follow `graphical-session.target`. Your session must manage that
target and provide desktop connection variables to the user manager; otherwise
use the desktop's session-start mechanism.

The units add `RUST_LOG=warn` and `--no-window-logging`; other command options
retain upstream defaults. The RPM does not add a confinement profile or change
SELinux policy. Use upstream's guides for runtime behavior and security
limitations, and test your intended device/session setup before deployment.

## Updates and removal

Upgrades preserve existing service enablement and do not request an automatic
restart. Restart deliberately after checking the new configuration.

Stop and disable the units you enabled before removal. The RPM retains
administrator configuration, drop-ins, per-user groups, and the service account.
Remove obsolete socket directories and local permission grants separately.
Reload udev rules or reboot after removal; existing device permissions and the
loaded uinput module need not disappear when their configuration is removed.

## Packaging and maintenance

### Build inputs

The spec pins v0.15.18 to commit
`23e880d441bf968de396c731fdcea18b1af62d9b` and verifies the source archive,
upstream lockfile, and replacement lockfile hashes. The only lockfile change
updates rustix 1.1.5 to 1.1.6 and its checksum.

| Fedora | Cargo and rustc |
| --- | --- |
| 44 | 1.99.1 |
| 45 | 1.100.0 |

Build and test with `--release --locked --no-default-features --features full`.
`device-test` is excluded. COPR networking must be enabled to fetch locked
crates. Retain buildroot package lists and artifact checksums because OS
tooling can affect the output.

### Dependency review and tests

On 2026-11-21, the full normal/build graphs contained the same 152 distinct
crates.io name/version pairs on both architectures. OSV returned four
previously recorded unmaintained-crate findings:

| Crate | Version | Advisory |
| --- | --- | --- |
| unsafe-libyaml | 0.2.11 | RUSTSEC-2024-0449 |
| zbus_names | 4.3.5 | RUSTSEC-2026-0371 |
| zvariant | 5.15.1 | RUSTSEC-2026-0370 |
| zvariant_derive | 5.15.1 | RUSTSEC-2026-0372 |

These accepted exceptions retain upstream YAML and zbus 5 support. Revisit
YAML when the parser is replaced or gated, and zbus at the next upstream
update. A zbus 6 migration needs source and service testing.

rustix 1.1.6 addresses RUSTSEC-2026-0486 and had no OSV finding. Using TOML
does not remove the compiled YAML dependency. Recheck advisories before
promotion against each target's graph:

```sh
cargo tree --locked --target TARGET-unknown-linux-gnu \
  --no-default-features --features full -e normal,build
```

Replace `TARGET` with `x86_64` or `aarch64`.

`%check` runs non-device Rust tests, desktop-feature assertions, and valid/invalid
configuration checks. PR builds also run `test-package.sh` to check installation,
account creation, unit/rule syntax, ownership, disabled defaults, state
preservation, and removal. **Run that script only in a disposable Fedora
container:** it writes `/etc` and removes the RPM. It never starts a remapper;
live device, desktop, and SELinux testing remain separate.

### Upstream references and Fedora adaptations

These links are pinned to the packaged commit, not the moving upstream branch.
Recheck them when updating the source. `README.md` is this Fedora guide,
installed as `README.fedora`; upstream's README, documentation, and example
mappings are installed separately without local edits.

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
| `README.md` | Guides above | Fedora guide, installed as `README.fedora`. |

The Dagger and PR-workflow changes are repository-owned build infrastructure,
not upstream installation files.

### COPR workflow

Use the existing `scottames/xremap` project. During PR #780 review, its SCM
package tracks `feat/sct-382-xremap`; switch it to `main` after merge.
Check for an existing build before requesting another:

```sh
copr-cli build-package --name xremap \
  --chroot fedora-44-x86_64 --chroot fedora-44-aarch64 \
  --chroot fedora-45-x86_64 --chroot fedora-45-aarch64 scottames/xremap
```

Rawhide is not an acceptance target for this change. Record build IDs,
packaging commit, chroots, RPM/SRPM SHA-256 checksums, and dependency findings
in [SCT-382](https://linear.app/ames/issue/SCT-382).

Scotty's deployment belongs to SCT-376. Discuss the `dots` versus `containers`
ownership split when that issue is worked; this package does not decide it.

[setup-config]: https://github.com/xremap/xremap/blob/v0.15.18/README.md#configuration
[setup-cli]: https://github.com/xremap/xremap/blob/v0.15.18/README.md#commandline-arguments
[setup-troubleshooting]: https://github.com/xremap/xremap/blob/v0.15.18/doc/troubleshooting.md
[setup-system]: https://github.com/xremap/xremap/blob/v0.15.18/doc/running_as_system_service.md
[setup-user]: https://github.com/xremap/xremap/blob/v0.15.18/doc/running_as_user_service.md
[setup-permissions]: https://github.com/xremap/xremap/blob/v0.15.18/doc/running_without_sudo.md
[setup-reboot]: https://github.com/xremap/xremap/blob/v0.15.18/doc/running_without_sudo.md#reboot-or-try-to-run-right-away-without-rebooting
[setup-groups]: https://github.com/xremap/xremap/blob/v0.15.18/doc/running_as_system_service.md#create-groups-for-socket-feature-optional
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

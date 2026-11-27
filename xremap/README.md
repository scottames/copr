# [xremap](https://github.com/xremap/xremap) for Fedora

A general-purpose xremap package for Fedora on x86_64 and aarch64,
built with upstream's `full` desktop support.

See the [COPR project](https://copr.fedorainfracloud.org/coprs/scottames/xremap/)
for available Fedora releases and builds.

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

For build controls, dependency review, tests, and upstream provenance, see
[Package maintenance](MAINTENANCE.md).

[setup-config]: https://github.com/xremap/xremap/blob/v0.15.18/README.md#configuration
[setup-cli]: https://github.com/xremap/xremap/blob/v0.15.18/README.md#commandline-arguments
[setup-troubleshooting]: https://github.com/xremap/xremap/blob/v0.15.18/doc/troubleshooting.md
[setup-system]: https://github.com/xremap/xremap/blob/v0.15.18/doc/running_as_system_service.md
[setup-user]: https://github.com/xremap/xremap/blob/v0.15.18/doc/running_as_user_service.md
[setup-permissions]: https://github.com/xremap/xremap/blob/v0.15.18/doc/running_without_sudo.md
[setup-reboot]: https://github.com/xremap/xremap/blob/v0.15.18/doc/running_without_sudo.md#reboot-or-try-to-run-right-away-without-rebooting
[setup-groups]: https://github.com/xremap/xremap/blob/v0.15.18/doc/running_as_system_service.md#create-groups-for-socket-feature-optional

#!/usr/bin/env bash
# Installs/removes packages and writes /etc. Run only in a disposable Fedora container.
# Fedora-authored package checks, not a copy of upstream's device test suite.
# Upstream CLI contracts and service setup provenance are in MAINTENANCE.md.
set -euo pipefail

if [[ ${PACKAGE_TEST_DISPOSABLE:-} != 1 || $EUID != 0 || $# != 1 ]]; then
  echo "Usage (root, disposable container only): PACKAGE_TEST_DISPOSABLE=1 bash $0 RPM" >&2
  exit 2
fi

package=$(realpath "$1")
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

# The test must start without an installed package or local configuration.
if rpm -q xremap; then
  echo "Start with a clean container without xremap installed" >&2
  exit 1
fi
test ! -e /etc/xremap
# Fedora's container image defaults to tsflags=nodocs; exercise the complete RPM.
dnf --setopt=tsflags= install -y --nogpgcheck "$package"

getent passwd xremap
getent group xremap
case "$(getent passwd xremap | cut -d: -f7)" in
  /sbin/nologin | /usr/sbin/nologin) ;;
  *) echo "Service account must not have a login shell" >&2; exit 1 ;;
esac
test "$(stat -c '%U:%G:%a' /etc/xremap)" = root:root:755
test ! -e /etc/xremap/config.yml
test ! -e /etc/xremap/config.toml
test "$(systemctl --root=/ is-enabled xremap.service || :)" = disabled
test "$(systemctl --global is-enabled xremap.service || :)" = disabled
test "$(systemctl --global is-enabled xremap-bridge.service || :)" = disabled

for path in \
  /usr/lib/systemd/system/xremap.service \
  /usr/lib/systemd/user/xremap.service \
  /usr/lib/systemd/user/xremap-bridge.service \
  /usr/lib/sysusers.d/xremap.conf \
  /usr/lib/modules-load.d/xremap.conf \
  /usr/lib/udev/rules.d/70-xremap.rules \
  /usr/share/bash-completion/completions/xremap \
  /usr/share/zsh/site-functions/_xremap \
  /usr/share/fish/vendor_completions.d/xremap.fish \
  /usr/share/doc/xremap/README.fedora \
  /usr/share/doc/xremap/MAINTENANCE.md \
  /usr/share/doc/xremap/doc/running_as_system_service.md; do
  test -s "$path"
  test "$(stat -c '%U:%G' "$path")" = root:root
done
rpm -V xremap
# Every packaged Documentation= URI must resolve without an upstream web request.
for unit in /usr/lib/systemd/system/xremap.service \
  /usr/lib/systemd/user/xremap.service /usr/lib/systemd/user/xremap-bridge.service; do
  while IFS= read -r uri; do
    test -s "${uri#file://}"
  done < <(sed -n 's/^Documentation=//p' "$unit")
done
udevadm verify /usr/lib/udev/rules.d/70-xremap.rules
systemd-analyze --man=no verify /usr/lib/systemd/system/xremap.service
install -d -m 0700 "$workdir/runtime"
XDG_RUNTIME_DIR="$workdir/runtime" systemd-analyze --user --man=no verify \
  /usr/lib/systemd/user/xremap.service /usr/lib/systemd/user/xremap-bridge.service

xremap --version
desktops=$(xremap --list-desktops)
for desktop in GNOME KDE Hypr wlroots Niri COSMIC Pantheon X11 Socket; do
  grep -qw "$desktop" <<< "$desktops"
done
xremap --validate-config /usr/share/doc/xremap/config.yml

# Check administrator state survives a replacement transaction. Do not start units.
printf 'modmap: []\nkeymap: []\n' > /etc/xremap/config.yml
systemctl --root=/ enable xremap.service
systemctl --global enable xremap-bridge.service
dnf --setopt=tsflags= reinstall -y --nogpgcheck "$package"
test "$(systemctl --root=/ is-enabled xremap.service)" = enabled
test "$(systemctl --global is-enabled xremap-bridge.service)" = enabled
printf 'modmap: []\nkeymap: []\n' | cmp - /etc/xremap/config.yml

# Removal must clean packaged files and enablement, not administrator data or UID.
dnf remove -y --noautoremove xremap
test ! -e /usr/bin/xremap
test ! -e /usr/lib/udev/rules.d/70-xremap.rules
test ! -e /etc/systemd/system/multi-user.target.wants/xremap.service
test ! -e /etc/systemd/user/graphical-session.target.wants/xremap-bridge.service
printf 'modmap: []\nkeymap: []\n' | cmp - /etc/xremap/config.yml
getent passwd xremap
echo "xremap package install, replacement, and removal checks passed"

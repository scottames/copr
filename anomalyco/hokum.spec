%global debug_package %{nil}

Name:           hokum
# Keep each architecture's version and checksum together for Renovate.
%ifarch x86_64
%global upstream_arch x64
%global upstream_rpm_sha256 53edcee247101ffa8715a32ca22e607b3b71a89031aa330abb8ad04d5c9d18e6
Version:        0.1.3
%endif
%ifarch aarch64
%global upstream_arch arm64
%global upstream_rpm_sha256 42dfbec4f6077126ed193dc79ebe75a6252a8bd2607bc6e9fd2e2bc9965bd42a
Version:        0.1.3
%endif
Release:        1%{?dist}
Summary:        Notification daemon for Wayland layer-shell compositors

License:        MIT
URL:            https://hokum.app
# Include both payloads in the SRPM so COPR can rebuild it on either architecture.
Source0:        https://github.com/anomalyco/hokum/releases/download/v%{version}/%{name}-%{version}-linux-x64.rpm
Source1:        https://github.com/anomalyco/hokum/releases/download/v%{version}/%{name}-%{version}-linux-arm64.rpm

%ifarch x86_64
%global upstream_rpm %{SOURCE0}
%else
%global upstream_rpm %{SOURCE1}
%endif

ExclusiveArch:  x86_64 aarch64

BuildRequires:  bsdtar
BuildRequires:  coreutils
BuildRequires:  desktop-file-utils
BuildRequires:  gawk
BuildRequires:  rpm
BuildRequires:  systemd-rpm-macros

# These libraries are loaded at runtime, so automatic ELF dependencies miss them.
Requires:       libvulkan.so.1()(64bit)
Requires:       libwayland-client.so.0()(64bit)
Provides:       desktop-notification-daemon
Recommends:     mesa-vulkan-drivers

%description
Hokum is a freedesktop notification daemon for Wayland compositors that
support the layer-shell protocol.

This COPR package republishes the official upstream GitHub Release RPM so
Fedora can install and update Hokum through DNF. It does not rebuild Hokum
from source.

%prep
%setup -q -c -T
echo '%{upstream_rpm_sha256}  %{upstream_rpm}' | sha256sum -c -
test "$(rpm -qp --qf '%%{NAME}' %{upstream_rpm})" = "%{name}"
test "$(rpm -qp --qf '%%{VERSION}' %{upstream_rpm})" = "%{version}"
test "$(rpm -qp --qf '%%{ARCH}' %{upstream_rpm})" = "%{_arch}"
rpmkeys --define '_pkgverify_level digest' --checksig %{upstream_rpm}

# Accept only regular files and directories before extracting the pinned RPM.
rpm -qp --qf '[%%{FILEMODES:octal}\t%%{FILENAMES}\n]' %{upstream_rpm} | awk '
    $1 ~ /^10[0-7]{4}$/ || $1 ~ /^4[0-7]{4}$/ { next }
    { print "ERROR: unsafe upstream RPM entry: " $2 > "/dev/stderr"; bad = 1 }
    END { exit bad }
'
mkdir payload
rpm2cpio %{upstream_rpm} | bsdtar -xf - -C payload \
    --no-same-owner --no-same-permissions

%build
# Upstream binary RPM repackaging; nothing to build.

%install
install -D -m 0755 payload/usr/bin/hokum %{buildroot}%{_bindir}/hokum
install -D -m 0644 payload/usr/lib/systemd/user/hokum.service \
    %{buildroot}%{_userunitdir}/hokum.service
install -D -m 0644 payload/usr/share/dbus-1/services/app.hokum.Notifications.service \
    %{buildroot}%{_datadir}/dbus-1/services/app.hokum.Notifications.service
install -D -m 0644 payload/usr/share/applications/hokum.desktop \
    %{buildroot}%{_datadir}/applications/hokum.desktop
install -D -m 0644 payload/usr/share/licenses/hokum/LICENSE \
    %{buildroot}%{_licensedir}/hokum/LICENSE

%check
test -x %{buildroot}%{_bindir}/hokum
desktop-file-validate %{buildroot}%{_datadir}/applications/hokum.desktop
grep -qx 'ExecStart=/usr/bin/hokum service' %{buildroot}%{_userunitdir}/hokum.service
grep -qx 'Name=org.freedesktop.Notifications' \
    %{buildroot}%{_datadir}/dbus-1/services/app.hokum.Notifications.service

%post
%systemd_user_post hokum.service

%preun
%systemd_user_preun hokum.service

%postun
%systemd_user_postun_with_restart hokum.service

%files
%license %{_licensedir}/hokum/LICENSE
%{_bindir}/hokum
%{_userunitdir}/hokum.service
%{_datadir}/dbus-1/services/app.hokum.Notifications.service
%{_datadir}/applications/hokum.desktop

%changelog
%autochangelog

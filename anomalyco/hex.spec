%global debug_package %{nil}

Name:           hex
# Keep each architecture's version and checksum together for Renovate.
%ifarch x86_64
%global upstream_arch x64
%global upstream_rpm_sha256 ff15519c6a4b9999afc828b9cf68c1478a4bc13457d74453c2d57a306680f353
Version:        3.3.0
%endif
%ifarch aarch64
%global upstream_arch arm64
%global upstream_rpm_sha256 89b67c52b31994cad6e8ae7d93d3c828d865dfaf40bd6b09c219761161e866a7
Version:        3.3.0
%endif
Release:        1%{?dist}
Summary:        Local voice dictation

License:        MIT
URL:            https://anoma.ly/hex
# Include both payloads in the SRPM so COPR can rebuild it on either architecture.
Source0:        https://github.com/anomalyco/hex/releases/download/v%{version}/%{name}-%{version}-linux-x64.rpm
Source1:        https://github.com/anomalyco/hex/releases/download/v%{version}/%{name}-%{version}-linux-arm64.rpm

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

# Include libraries loaded at runtime as well as automatic ELF dependencies.
Requires:       alsa-lib
Requires:       curl
Requires:       libvulkan.so.1()(64bit)
Requires:       libxkbcommon
Requires:       libxkbcommon-x11
Requires:       libX11
Requires:       libxcb
Requires:       libXcursor
Requires:       libXi
Requires:       libwayland-client.so.0()(64bit)
Recommends:     mesa-vulkan-drivers
Recommends:     wl-clipboard
Recommends:     wtype
Recommends:     xdg-utils

%description
Hex provides local voice dictation. Hold a shortcut, speak, and release it
to transcribe speech on your device and paste it into the active application.
The first run downloads a speech model.

This COPR package republishes the official upstream GitHub Release RPM so
Fedora can install and update Hex through DNF. It does not rebuild Hex from
source.

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
install -D -m 0755 payload/usr/bin/hex %{buildroot}%{_bindir}/hex
install -D -m 0644 payload/usr/lib/systemd/user/hex.service \
    %{buildroot}%{_userunitdir}/hex.service
install -D -m 0644 payload/usr/share/applications/anomaly.hex.desktop \
    %{buildroot}%{_datadir}/applications/anomaly.hex.desktop
for size in 16 24 32 48 64 128 256 512; do
    install -D -m 0644 "payload/usr/share/icons/hicolor/${size}x${size}/apps/anomaly.hex.png" \
        "%{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/anomaly.hex.png"
done
install -D -m 0644 payload/usr/share/licenses/hex/LICENSE \
    %{buildroot}%{_licensedir}/hex/LICENSE

%check
test -x %{buildroot}%{_bindir}/hex
desktop-file-validate %{buildroot}%{_datadir}/applications/anomaly.hex.desktop
grep -q '^ExecStart=/usr/bin/hex' %{buildroot}%{_userunitdir}/hex.service
for size in 16 24 32 48 64 128 256 512; do
    test -s "%{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/anomaly.hex.png"
done

%post
%systemd_user_post hex.service

%preun
%systemd_user_preun hex.service

%postun
%systemd_user_postun_with_restart hex.service

%files
%license %{_licensedir}/hex/LICENSE
%{_bindir}/hex
%{_userunitdir}/hex.service
%{_datadir}/applications/anomaly.hex.desktop
%{_datadir}/icons/hicolor/*/apps/anomaly.hex.png

%changelog
%autochangelog

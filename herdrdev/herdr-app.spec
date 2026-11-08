%global core_min 0.1.11
%global debug_package %{nil}

Name:           herdr-app
# Keep each architecture's version and checksum together for Renovate.
%ifarch x86_64
%global upstream_arch x86_64
%global upstream_sha256 475a383f8f439e3191a86635b5c1286ce4dfd2d9fcdf1e7cbdfdd6c7176f8ff3
Version:        0.1.14
%endif
%ifarch aarch64
%global upstream_arch aarch64
%global upstream_sha256 30a431ce95c17356efe8afed50c4eaf8888d83ef45acd9aa911094d51707d007
Version:        0.1.14
%endif
Release:        1%{?dist}
Summary:        Desktop app for persistent terminals and coding agents

License:        Apache-2.0
URL:            https://github.com/herdrdev/herdr-app
# Include both payloads in the SRPM so COPR can rebuild it on either architecture.
Source0:        https://releases.herdr.dev/app/%{version}/%{name}-linux-x86_64.tar.gz
Source1:        https://releases.herdr.dev/app/%{version}/%{name}-linux-aarch64.tar.gz
Source2:        https://releases.herdr.dev/app/%{version}/manifest.json#/%{name}-%{version}-manifest.json
Source3:        herdr-app.desktop

%ifarch x86_64
%global upstream_source %{SOURCE0}
%else
%global upstream_source %{SOURCE1}
%endif

ExclusiveArch:  x86_64 aarch64

BuildRequires:  coreutils
BuildRequires:  desktop-file-utils
BuildRequires:  fontconfig
BuildRequires:  jq
BuildRequires:  libgcc
BuildRequires:  libxcb
BuildRequires:  libxkbcommon
BuildRequires:  libxkbcommon-x11
BuildRequires:  tar

Requires:       herdr-core%{?_isa} >= %{core_min}
# Include libraries loaded at runtime as well as automatic ELF dependencies.
Requires:       curl
Requires:       fontconfig
Requires:       hicolor-icon-theme
Requires:       libvulkan.so.1()(64bit)
Requires:       libwayland-client.so.0()(64bit)
Recommends:     mesa-vulkan-drivers

%description
Herdr is a desktop app for terminals and coding agents. Its separate herdr-core
runtime keeps terminals running when the window closes.

This COPR package repackages the official upstream Linux binaries. It does not
build Herdr from source or run upstream's installation scripts. Updates are
managed through DNF rather than the app's self-updater.

%prep
%setup -q -c -T
echo '%{upstream_sha256}  %{upstream_source}' | sha256sum -c -
jq -e --arg version '%{version}' --arg arch '%{upstream_arch}' \
    --arg sha '%{upstream_sha256}' --arg core_min '%{core_min}' \
    '.version == $version and .core_min == $core_min and
     .targets["linux-" + $arch].sha256 == $sha' %{SOURCE2}
tar -xzf %{upstream_source} --no-same-owner --no-same-permissions

%build
# Upstream binary repackaging; nothing to build.

%install
install -Dpm 0755 herdr-app/herdr-app %{buildroot}%{_bindir}/herdr-app
install -Dpm 0644 %{SOURCE3} %{buildroot}%{_datadir}/applications/herdr-app.desktop
# The Linux updater recognizes a release only when this icon is beside the
# executable. Keep it in the standard icon directory, not beside /usr/bin/herdr-app.
install -Dpm 0644 herdr-app/herdr-app.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/herdr-app.svg

%check
test "$(%{buildroot}%{_bindir}/herdr-app --version)" = 'herdr-app %{version}'
test ! -e %{buildroot}%{_bindir}/herdr-app.svg
test -s %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/herdr-app.svg
test -s herdr-app/LICENSE
test -s herdr-app/THIRD-PARTY-NOTICES
desktop-file-validate %{buildroot}%{_datadir}/applications/herdr-app.desktop

%files
%license herdr-app/LICENSE herdr-app/THIRD-PARTY-NOTICES
%{_bindir}/herdr-app
%{_datadir}/applications/herdr-app.desktop
%{_datadir}/icons/hicolor/scalable/apps/herdr-app.svg

%changelog
%autochangelog

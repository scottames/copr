%global debug_package %{nil}

Name:           herdr-core
# Keep each architecture's version and checksum together for Renovate.
%ifarch x86_64
%global upstream_arch x86_64
%global upstream_sha256 5b2f97cb4b2a9d7a6b2cc5942628203ed9fbb7cc0c2b4b09ad8a6f5648e246b7
Version:        0.1.18
%endif
%ifarch aarch64
%global upstream_arch aarch64
%global upstream_sha256 cf33393cf950bb763734dc3e16610ab9daf8492391a4ef0de56026cd7f752853
Version:        0.1.18
%endif
Release:        1%{?dist}
Summary:        Persistent terminal runtime for coding agents

License:        Apache-2.0
URL:            https://github.com/herdrdev/herdr-core
# Include both payloads in the SRPM so COPR can rebuild it on either architecture.
Source0:        https://releases.herdr.dev/core/%{version}/%{name}-linux-x86_64.tar.gz
Source1:        https://releases.herdr.dev/core/%{version}/%{name}-linux-aarch64.tar.gz
Source2:        https://releases.herdr.dev/core/%{version}/manifest.json#/%{name}-%{version}-manifest.json

%ifarch x86_64
%global upstream_source %{SOURCE0}
%else
%global upstream_source %{SOURCE1}
%endif

ExclusiveArch:  x86_64 aarch64

BuildRequires:  coreutils
BuildRequires:  jq
BuildRequires:  tar

Recommends:     openssh-clients
Recommends:     systemd

%description
Herdr Core runs programs and coding agents in persistent terminals. It provides
the hc command and the runtime used by herdr-app, and can also be used on its own.

This COPR package repackages the official upstream static Linux binaries. It
does not build Herdr Core from source or run upstream's installation scripts.
Run the core as your regular user; it starts on demand.

%prep
%setup -q -c -T
echo '%{upstream_sha256}  %{upstream_source}' | sha256sum -c -
# A new protocol generation needs a matching app and a reviewed dependency range.
jq -e --arg version '%{version}' --arg arch '%{upstream_arch}' \
    --arg sha '%{upstream_sha256}' \
    '.version == $version and .generation == 1 and
     .targets["linux-" + $arch].sha256 == $sha' %{SOURCE2}
tar -xzf %{upstream_source} --no-same-owner --no-same-permissions

%build
# Upstream binary repackaging; nothing to build.

%install
install -Dpm 0755 herdr-core %{buildroot}%{_bindir}/herdr-core
ln -s herdr-core %{buildroot}%{_bindir}/hc

%check
test "$(%{buildroot}%{_bindir}/herdr-core --version)" = 'hc %{version}'
test "$(%{buildroot}%{_bindir}/hc --version)" = 'hc %{version}'
test "$(readlink %{buildroot}%{_bindir}/hc)" = herdr-core
test -s LICENSE
test -s THIRD-PARTY-NOTICES

%files
%license LICENSE THIRD-PARTY-NOTICES
%{_bindir}/herdr-core
%{_bindir}/hc

%changelog
%autochangelog

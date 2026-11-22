%global debug_package %{nil}

Name:           herdr-core
# Keep each architecture's version and checksum together for Renovate.
%ifarch x86_64
%global upstream_arch x86_64
%global upstream_sha256 3054ec3992ce80c5715d721caa9dcefa6056721d15dc113f4750afce763ba5df
Version:        0.1.22
%endif
%ifarch aarch64
%global upstream_arch aarch64
%global upstream_sha256 98757985245d45f8d73dd85e68b139b7f167c28488bb89edd9834c3f5a5cf4cf
Version:        0.1.22
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

%global debug_package %{nil}

Name:           zig017
Version:        0.17.0
Release:        %autorelease
Summary:        General-purpose programming language and toolchain

License:        MIT
URL:            https://ziglang.org
Source0:        https://ziglang.org/download/%{version}/zig-x86_64-linux-%{version}.tar.xz
Source1:        https://ziglang.org/download/%{version}/zig-aarch64-linux-%{version}.tar.xz

%ifarch x86_64
%global upstream_source %{SOURCE0}
%global upstream_sha256 1cbe9df9f27e6b78d14ccbca43b6703a404ef79ef1c463de901d7f088d4e2026
%endif
%ifarch aarch64
%global upstream_source %{SOURCE1}
%global upstream_sha256 9e8d11661d4ae3bd57702a3832781e23ad151dde5798e16a5ccd503f65234ff8
%endif

ExclusiveArch:  x86_64 aarch64

BuildRequires:  coreutils

%description
Zig is a general-purpose programming language and toolchain for maintaining
robust, optimal, and reusable software.

This package repackages the official upstream prebuilt compiler so Ghostty can
be built with Zig %{version}, independently of Fedora's default Zig release.

%prep
%setup -q -c -T -n zig-%{version}

actual_sum="$(sha256sum %{upstream_source} | cut -d' ' -f1)"
if [ "%{upstream_sha256}" != "$actual_sum" ]; then
    echo "ERROR: checksum verification failed for %{upstream_source}" >&2
    echo "Expected: %{upstream_sha256}" >&2
    echo "Actual:   $actual_sum" >&2
    exit 1
fi

tar -xf %{upstream_source} --strip-components=1

%build
# Upstream prebuilt compiler repackaging; nothing to build.

%install
install -Dpm 0755 zig %{buildroot}%{_bindir}/zig
mkdir -p %{buildroot}%{_prefix}/lib
cp -a lib %{buildroot}%{_prefix}/lib/zig

%check
test "$(%{buildroot}%{_bindir}/zig version)" = "%{version}"

%files
%license LICENSE
%doc README.md
%{_bindir}/zig
%{_prefix}/lib/zig/

%changelog
%autochangelog

%global debug_package %{nil}

%ifarch x86_64
%global zig_arch x86_64
%global upstream_sha256 02aa270f183da276e5b5920b1dac44a63f1a49e55050ebde3aecc9eb82f93239
%endif
%ifarch aarch64
%global zig_arch aarch64
%global upstream_sha256 958ed7d1e00d0ea76590d27666efbf7a932281b3d7ba0c6b01b0ff26498f667f
%endif

Name:           zig015
Version:        0.15.2
Release:        %autorelease
Summary:        General-purpose programming language and toolchain

License:        MIT
URL:            https://ziglang.org
Source0:        https://ziglang.org/download/%{version}/zig-%{zig_arch}-linux-%{version}.tar.xz

ExclusiveArch:  x86_64 aarch64

BuildRequires:  coreutils

%description
Zig is a general-purpose programming language and toolchain for maintaining
robust, optimal, and reusable software.

This package repackages the official upstream prebuilt compiler so Ghostty can
be built with Zig %{version}, rather than Fedora's newer Zig release.

%prep
%setup -q -n zig-%{zig_arch}-linux-%{version}

actual_sum="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
if [ "%{upstream_sha256}" != "$actual_sum" ]; then
    echo "ERROR: checksum verification failed for %{SOURCE0}" >&2
    echo "Expected: %{upstream_sha256}" >&2
    echo "Actual:   $actual_sum" >&2
    exit 1
fi

%build
# Upstream prebuilt compiler repackaging; nothing to build.

%install
install -Dpm 0755 zig %{buildroot}%{_bindir}/zig
mkdir -p %{buildroot}%{_libdir}
cp -a lib %{buildroot}%{_libdir}/zig

%check
test "$(%{buildroot}%{_bindir}/zig version)" = "%{version}"

%files
%license LICENSE
%doc README.md
%{_bindir}/zig
%{_libdir}/zig/

%changelog
%autochangelog

%global upstream_source_sha256 a82209aaef3534407f29d860e3174974f19b4a7c10286212fdeacdcd1cb9049d

Name:           monstar
Version:        1.0.1
Release:        %autorelease
Summary:        Linux-native Wayland terminal built on the Ghostty terminal core

License:        MIT
URL:            https://github.com/rockorager/monstar
Source0:        https://github.com/rockorager/monstar/releases/download/v%{version}/monstar-%{version}-source.tar.gz

ExclusiveArch:  x86_64 aarch64

BuildRequires:  coreutils
BuildRequires:  fontconfig-devel
BuildRequires:  freetype-devel
BuildRequires:  git-core
BuildRequires:  harfbuzz-devel
BuildRequires:  libxkbcommon-devel
BuildRequires:  ncurses
BuildRequires:  pkg-config
BuildRequires:  wayland-devel >= 1.25
BuildRequires:  wayland-protocols-devel >= 1.49
BuildRequires:  zig >= 0.16.0

%description
Monstar is a terminal emulator for Linux and Wayland built on the Ghostty
terminal core. It supports fractional scaling, text input, desktop
notifications, Kitty graphics, scrollback search, and bundled color schemes.

%prep
actual_sum="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
if [ "%{upstream_source_sha256}" != "$actual_sum" ]; then
    echo "ERROR: checksum verification failed for %{SOURCE0}" >&2
    echo "Expected: %{upstream_source_sha256}" >&2
    echo "Actual:   $actual_sum" >&2
    exit 1
fi

%autosetup -n %{name}-%{version}

%build
# The release source archive does not vendor the Zig dependency tree.
zig build --fetch=all
zig build \
    --summary all \
    --build-id=sha1 \
    -Doptimize=ReleaseFast \
    -Dcpu=baseline

%install
mkdir -p %{buildroot}%{_prefix}
cp -a zig-out/. %{buildroot}%{_prefix}/

%check
test "$(%{buildroot}%{_bindir}/monstar --version)" = "monstar %{version}"

%files
%license LICENSE
%doc README.md
%{_bindir}/monstar
%{_datadir}/applications/dev.rockorager.monstar.desktop
%{_datadir}/icons/hicolor/scalable/apps/dev.rockorager.monstar.svg
%{_datadir}/monstar/
%{_mandir}/man1/monstar.1*
%{_mandir}/man5/monstar.5*

%changelog
%autochangelog

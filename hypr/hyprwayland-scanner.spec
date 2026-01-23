Name:           hyprwayland-scanner
Version:        0.4.5
# -b1: patch for protocol-specific dummy_type names
Release:        %autorelease -b1
Summary:        A Hyprland implementation of wayland-scanner, in and for C++

License:        BSD-3-Clause
URL:            https://github.com/hyprwm/hyprwayland-scanner
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
# Fix protocol-specific dummy_type names for hyprpaper 0.8.1 compatibility
# https://github.com/hyprwm/hyprwayland-scanner/commit/b3b0f1f
# Remove when updating to >= 0.4.6
Source1:        %{url}/commit/b3b0f1f40ae09d4447c20608e5a4faf8bf3c492d.patch

# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch:    %{ix86}

BuildRequires:  cmake
BuildRequires:  cmake(pugixml)
BuildRequires:  gcc-c++

%description
%{summary}.

%package        devel
Summary:        A Hyprland implementation of wayland-scanner, in and for C++

%description    devel
%{summary}.

%prep
%autosetup -p1
patch -p1 < %{SOURCE1}

%build
%cmake
%cmake_build

%install
%cmake_install

%files devel
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_libdir}/pkgconfig/%{name}.pc
%{_libdir}/cmake/%{name}/

%changelog
%autochangelog

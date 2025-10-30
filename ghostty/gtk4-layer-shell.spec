# Disable tests - they require a Wayland display server and GPU/DRM devices
# which are not available in container builds
%bcond_with check

Name:           gtk4-layer-shell
Version:        1.3.0
Release:        %autorelease
Summary:        Library to create panels and other desktop components for Wayland

License:        MIT
URL:            https://github.com/wmww/gtk4-layer-shell
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  meson >= 0.54.0
BuildRequires:  vala
BuildRequires:  pkgconfig(gobject-introspection-1.0)
BuildRequires:  pkgconfig(gtk4)
BuildRequires:  pkgconfig(wayland-client) >= 1.10.0
BuildRequires:  pkgconfig(wayland-protocols) >= 1.16
BuildRequires:  pkgconfig(wayland-scanner) >= 1.10.0
BuildRequires:  pkgconfig(wayland-server) >= 1.10.0
%if %{with check}
BuildRequires:  python3-gobject
### For smoke tests
# BuildRequires:  luarocks
# BuildRequires:  pkgconfig(luajit)
%endif

%description
A library for using the Layer Shell Wayland protocol with GTK4. With this
library you can build desktop shell components such as panels, notifications
and wallpapers. You can use it to anchor your windows to a corner or edge of
the output, or stretch them across the entire output. This Library is
compatible with C, C++ and any language that supports GObject introspection
files (Python, Vala, etc).

%package        devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    devel
Development files for %{name}.

%prep
%autosetup

%build
# Disable smoke tests since they introduce two problems:
#   1. They need the examples which will be installed and check-files fails with
#      the error 'Installed (but unpackaged) file(s) found'
#   2. The lua-lgi package is based on the (latest) release from 2017 which does
#      not work with GTK4.
# See also:
#   - https://github.com/wmww/gtk4-layer-shell/issues/28
#   - https://github.com/wmww/gtk4-layer-shell/issues/32#issuecomment-2089302515
#   - https://github.com/lgi-devs/lgi/issues/225
#   - https://github.com/lgi-devs/lgi/issues/278
%meson \
    %if %{with check}
    -Dsmoke-tests=false \
    -Dtests=true \
    %endif
    %{nil}
%meson_build

%install
%meson_install

%if %{with check}
%check
%meson_test
%endif

%files
%license LICENSE
%doc README.md CHANGELOG.md
%{_libdir}/girepository-1.0/Gtk4LayerShell-*.typelib
%{_libdir}/girepository-1.0/Gtk4SessionLock-*.typelib
%{_libdir}/lib%{name}.so.%{version}
%{_libdir}/lib%{name}.so.0
%{_libdir}/liblayer-shell-preload.so

%files devel
%{_datadir}/gir-1.0/Gtk4LayerShell-*.gir
%{_datadir}/gir-1.0/Gtk4SessionLock-*.gir
%{_datadir}/vala/vapi/%{name}-*
%{_includedir}/%{name}/
%{_libdir}/lib%{name}.so
%{_libdir}/pkgconfig/*.pc
%{_libdir}/liblayer-shell-preload.so

%changelog
%autochangelog

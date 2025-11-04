%global forgeurl https://github.com/vicinaehq/vicinae
%global debug_package %{nil}

Name:           vicinae
Epoch:          1
Version:        0.16.1
Release:        1%{?dist}
Summary:        A focused launcher for your desktop — native, fast, extensible
License:        GPL-3.0

%forgemeta
URL:            %{forgeurl}
Source0:        %{forgesource}
BuildRequires:  cmake
BuildRequires:  ninja-build
BuildRequires:  desktop-file-utils

BuildRequires:  cmake(Qt6)
BuildRequires:  cmake(Qt6Svg)
BuildRequires:  cmake(Qt6WaylandClient)
BuildRequires:  cmake(Qt6Widgets)
BuildRequires:  cmake(Qt6Keychain)
BuildRequires:  cmake(LayerShellQt)
BuildRequires:  cmake(rapidfuzz)
BuildRequires:  cmake(absl)

BuildRequires:  pkgconfig(libcmark-gfm)
BuildRequires:  pkgconfig(libqalculate)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(protobuf)

BuildRequires:  nodejs-npm
BuildRequires:  minizip-compat-devel
BuildRequires:  qt6-qtbase-private-devel

Recommends:     vicinae-icon-theme


%description
Vicinae (pronounced "vih-SIN-ay") is a high-performance, native launcher for your desktop — built with C++ and Qt.

It includes a set of built-in modules, and extensions can be developed quickly using fully server-side React/TypeScript — with no browser or Electron involved.

Inspired by the popular Raycast launcher, Vicinae provides a mostly compatible extension API, allowing reuse of many existing Raycast extensions with minimal modification.

Vicinae is designed for developers and power users who want fast, keyboard-first access to common system actions — without unnecessary overhead.


%package icon-theme
Summary:        vicinae icon theme
License:        GPL-3.0
BuildArch:      noarch

%description icon-theme
Vicinae icon theme


%prep
%forgeautosetup


%build
%cmake -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
%cmake_build


%install
sed -i '/^Terminal=False$/d' extra/vicinae.desktop
sed -i 's/Terminal=False/Terminal=false/' extra/vicinae.desktop
sed -i 's/^Categories=.*/Categories=Utility;/' extra/vicinae.desktop
%cmake_install
install -Dm644 extra/vicinae.service %{buildroot}%{_userunitdir}/vicinae.service
install -Dm644 vicinae/icons/vicinae.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/vicinae.svg


%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop


%files
%{_bindir}/vicinae
%{_bindir}/vicinae-wlr-clip
%{_datadir}/applications/*.desktop
%{_userunitdir}/vicinae.service
%{_datadir}/icons/hicolor/scalable/apps/vicinae.svg
%{_datadir}/vicinae/themes/*


%files icon-theme
%{_datadir}/icons/vicinae/index.theme
%{_datadir}/icons/vicinae/8x8/
%{_datadir}/icons/vicinae/16x16/
%{_datadir}/icons/vicinae/16x16@2x
%{_datadir}/icons/vicinae/18x18/
%{_datadir}/icons/vicinae/18x18@2x
%{_datadir}/icons/vicinae/22x22/
%{_datadir}/icons/vicinae/22x22@2x
%{_datadir}/icons/vicinae/24x24/
%{_datadir}/icons/vicinae/24x24@2x
%{_datadir}/icons/vicinae/32x32/
%{_datadir}/icons/vicinae/32x32@2x
%{_datadir}/icons/vicinae/42x42/
%{_datadir}/icons/vicinae/48x48/
%{_datadir}/icons/vicinae/48x48@2x
%{_datadir}/icons/vicinae/64x64/
%{_datadir}/icons/vicinae/64x64@2x
%{_datadir}/icons/vicinae/84x84/
%{_datadir}/icons/vicinae/96x96/
%{_datadir}/icons/vicinae/128x128/

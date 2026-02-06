%global forgeurl https://github.com/vicinaehq/vicinae
%global debug_package %{nil}

Name:           vicinae
Epoch:          1
Version:        0.19.6
Release:        1%{?dist}
Summary:        A focused launcher for your desktop — native, fast, extensible
License:        GPL-3.0

%forgemeta
URL:            %{forgeurl}
Source0:        %{forgesource}
BuildRequires:  cmake
BuildRequires:  git
BuildRequires:  ninja-build
BuildRequires:  desktop-file-utils
BuildRequires:  wayland-devel

BuildRequires:  cmake(Qt6)
BuildRequires:  cmake(Qt6Svg)
BuildRequires:  cmake(Qt6WaylandClient)
BuildRequires:  cmake(Qt6Widgets)
BuildRequires:  cmake(Qt6Keychain)
BuildRequires:  cmake(LayerShellQt)
BuildRequires:  cmake(rapidfuzz)
BuildRequires:  cmake(absl)
BuildRequires:  glaze

BuildRequires:  pkgconfig(icu-uc)
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
COMMIT_HASH="$(git -C %{_builddir}/%{extractdir} rev-parse --short=7 HEAD 2>/dev/null || echo "unknown")"

%cmake -G Ninja \
    -DVICINAE_GIT_TAG="v%{version}" \
    -DVICINAE_GIT_COMMIT_HASH="${COMMIT_HASH}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DVICINAE_PROVENANCE=copr \
    -DUSE_SYSTEM_GLAZE=ON \
%cmake_build


%install
sed -i '/^Terminal=False$/d' extra/vicinae.desktop
sed -i 's/Terminal=False/Terminal=false/' extra/vicinae.desktop
sed -i 's/^Categories=.*/Categories=Utility;/' extra/vicinae.desktop
%cmake_install
install -Dm644 extra/vicinae.service %{buildroot}%{_userunitdir}/vicinae.service


%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop


%files
%{_bindir}/vicinae
%{_libexecdir}/vicinae/*
%{_sysconfdir}/chromium/native-messaging-hosts/com.vicinae.vicinae.json
/usr/lib/mozilla/native-messaging-hosts/com.vicinae.vicinae.json
%{_datadir}/applications/*.desktop
%{_userunitdir}/vicinae.service
%{_datadir}/icons/hicolor/512x512/apps/vicinae.png
%{_datadir}/vicinae/themes/*


%changelog
%autochangelog

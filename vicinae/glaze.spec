%global forgeurl https://github.com/stephenberry/glaze

Name:           glaze
Version:        9.0.0
Release:        %autorelease -b2
Summary:        Extremely fast, in memory, JSON and interface library for modern C++
License:        MIT

%forgemeta
URL:            %{forgeurl}
Source0:        %{forgesource}
# Backport https://github.com/stephenberry/glaze/pull/2977 for Qt consumers.
# patch-guard: remove-after-version=9.0.0 reason=qt-emit-macro-collision
Patch0:         glaze-9.0.0-qt-emit-macro.patch

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  ninja-build

BuildArch:      noarch

%description
Glaze is one of the fastest JSON libraries in the world, providing
serialization and deserialization for C++ structures. It's a header-only
library supporting JSON, BEVE, CBOR, CSV, MessagePack, TOML, and EETF formats.


%prep
%autosetup -n %{extractdir} -p1


%build
%cmake -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -Dglaze_DEVELOPER_MODE=OFF \
    -Dbuild_testing=OFF
%cmake_build


%install
%cmake_install


%files
%license LICENSE
%doc README.md
%{_includedir}/glaze/
%{_datadir}/glaze/


%changelog
%autochangelog

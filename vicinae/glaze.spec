%global forgeurl https://github.com/stephenberry/glaze

Name:           glaze
Version:        7.0.1
Release:        1%{?dist}
Summary:        Extremely fast, in memory, JSON and interface library for modern C++
License:        MIT

%forgemeta
URL:            %{forgeurl}
Source0:        %{forgesource}

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  ninja-build

BuildArch:      noarch

%description
Glaze is one of the fastest JSON libraries in the world, providing
serialization and deserialization for C++ structures. It's a header-only
library supporting JSON, BEVE, CBOR, CSV, MessagePack, TOML, and EETF formats.


%prep
%forgeautosetup


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

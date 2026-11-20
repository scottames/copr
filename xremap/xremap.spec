%global commit 23e880d441bf968de396c731fdcea18b1af62d9b
%global cargo_args --release --locked --no-default-features --features socket,niri
%if 0%{?fedora} == 44
%global rust_version 1.99.1
%else
%global rust_version 1.100.0
%endif

Name:           xremap
Version:        0.15.18
Release:        1%{?dist}
Summary:        Linux key remapper with socket and Niri desktop support
License:        MIT
URL:            https://github.com/xremap/xremap
Source0:        https://codeload.github.com/xremap/xremap/tar.gz/%{commit}#/%{name}-%{commit}.tar.gz
Source1:        Cargo.lock
ExclusiveArch:  x86_64
BuildRequires:  cargo = %{rust_version}
BuildRequires:  rust = %{rust_version}
BuildRequires:  gcc

%description
Remap Linux input events using application-specific rules. This build supports
a separate desktop bridge for Niri and a socket-connected input service.

%prep
echo '57580f9ee21215f8c8ee36c741cf9ef46aefad8d22c5938491f35e7398127216  %{SOURCE0}' | sha256sum -c -
%setup -q -n %{name}-%{commit}
echo '4aa9bb61b6f595b70de9d2a0494dc37b0110ffc02cdd3cda4e50de04347854d9  Cargo.lock' | sha256sum -c -
cp %{SOURCE1} Cargo.lock
echo 'b31fb7e3344b1e8c34118bbfb8eb0b294c346845ef15fa1ba9f183c12a5152b8  Cargo.lock' | sha256sum -c -

%build
cargo build %{cargo_args} --bin xremap

%install
install -Dpm755 target/release/xremap %{buildroot}%{_bindir}/xremap

%check
cargo test %{cargo_args}
%{buildroot}%{_bindir}/xremap --version

%files
%license LICENSE
%doc README.md
%{_bindir}/xremap

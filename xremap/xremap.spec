# Source controls live here; provenance and update procedures are in MAINTENANCE.md.
%global cargo_args --release --locked --no-default-features --features full
%global rust_version 1.100.0

Name:           xremap
%global commit 5bb2b582cd603d3467b61cd8aca259898d113ec3
Version:        0.15.19
Release:        %autorelease
Summary:        Linux key remapper with X11 and Wayland desktop support
License:        MIT
URL:            https://github.com/xremap/xremap
Source0:        https://codeload.github.com/xremap/xremap/tar.gz/%{commit}#/%{name}-%{commit}.tar.gz
# Reviewed for this release: upstream still locks rustix 1.1.5; patch applies unchanged.
# patch-guard: remove-after-version=0.15.19 reason=rustix-security-fix
Patch0:         xremap-rustix.patch
Source2:        README.md
Source3:        xremap.service
Source4:        xremap-user.service
Source5:        xremap-bridge.service
Source6:        xremap-sysusers.conf
Source7:        xremap-modules.conf
Source8:        70-xremap.rules
Source9:        80-xremap.preset
Source10:       MAINTENANCE.md
ExclusiveArch:  x86_64 aarch64
BuildRequires:  cargo = %{rust_version}
BuildRequires:  rust = %{rust_version}
BuildRequires:  gcc
BuildRequires:  systemd
BuildRequires:  systemd-rpm-macros
Requires:       systemd-udev
%{?systemd_requires}

%description
Remap Linux input events using application-specific rules. This is upstream's
full build, supporting X11, GNOME, KDE, Hyprland, wlroots, Niri, COSMIC,
Pantheon, and a socket-connected system input service with a desktop bridge.
Services and device-access setup are included but services are not enabled
on installation. Configure a service mode and mappings before starting xremap.

%prep
%autosetup -p1 -n %{name}-%{commit}
# A version-only bot update must not build the previous source commit.
grep -Fx 'version = "%{version}"' Cargo.toml
cp %{SOURCE2} README.fedora
cp %{SOURCE10} MAINTENANCE.md

%build
cargo build %{cargo_args} --bin xremap

%install
install -Dpm755 target/release/xremap %{buildroot}%{_bindir}/xremap
install -Dpm644 %{SOURCE3} %{buildroot}%{_unitdir}/xremap.service
install -Dpm644 %{SOURCE4} %{buildroot}%{_userunitdir}/xremap.service
install -Dpm644 %{SOURCE5} %{buildroot}%{_userunitdir}/xremap-bridge.service
install -Dpm644 %{SOURCE6} %{buildroot}%{_sysusersdir}/xremap.conf
install -Dpm644 %{SOURCE7} %{buildroot}%{_modulesloaddir}/xremap.conf
install -Dpm644 %{SOURCE8} %{buildroot}%{_udevrulesdir}/70-xremap.rules
install -Dpm644 %{SOURCE9} %{buildroot}%{_presetdir}/80-xremap.preset
install -Dpm644 %{SOURCE9} %{buildroot}%{_userpresetdir}/80-xremap.preset
install -dm755 %{buildroot}%{_sysconfdir}/xremap

mkdir -p completions
target/release/xremap --completions bash > completions/xremap.bash
target/release/xremap --completions zsh > completions/_xremap
target/release/xremap --completions fish > completions/xremap.fish
install -Dpm644 completions/xremap.bash %{buildroot}%{_datadir}/bash-completion/completions/xremap
install -Dpm644 completions/_xremap %{buildroot}%{_datadir}/zsh/site-functions/_xremap
install -Dpm644 completions/xremap.fish %{buildroot}%{_datadir}/fish/vendor_completions.d/xremap.fish

%check
cargo test %{cargo_args}
%{buildroot}%{_bindir}/xremap --version
desktops=$(%{buildroot}%{_bindir}/xremap --list-desktops)
for desktop in GNOME KDE Hypr wlroots Niri COSMIC Pantheon X11 Socket; do
    echo "$desktops" | grep -qw "$desktop"
done
%{buildroot}%{_bindir}/xremap --validate-config example/config.yml
printf 'modmap = []\nkeymap = []\n' > empty.toml
%{buildroot}%{_bindir}/xremap --validate-config empty.toml
printf 'modmap: [\n' > invalid.yml
if %{buildroot}%{_bindir}/xremap --validate-config invalid.yml; then
    echo 'Invalid configuration unexpectedly passed validation' >&2
    exit 1
fi

%post
%systemd_post xremap.service
%systemd_user_post xremap.service xremap-bridge.service

%preun
%systemd_preun xremap.service
%systemd_user_preun xremap.service xremap-bridge.service

%postun
%systemd_postun xremap.service
%systemd_user_postun xremap.service xremap-bridge.service

%files
%license LICENSE
%doc README.md README.fedora MAINTENANCE.md doc example/config.yml example/emacs.yml
%{_bindir}/xremap
%{_unitdir}/xremap.service
%{_userunitdir}/xremap.service
%{_userunitdir}/xremap-bridge.service
%{_sysusersdir}/xremap.conf
%{_modulesloaddir}/xremap.conf
%{_udevrulesdir}/70-xremap.rules
%{_presetdir}/80-xremap.preset
%{_userpresetdir}/80-xremap.preset
%dir %{_sysconfdir}/xremap
%{_datadir}/bash-completion/completions/xremap
%{_datadir}/zsh/site-functions/_xremap
%{_datadir}/fish/vendor_completions.d/xremap.fish

%changelog
%autochangelog

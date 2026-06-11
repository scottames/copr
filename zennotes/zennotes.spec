%global upstream_deb ZenNotes-%{version}-linux-amd64.deb
%global upstream_deb_sha256 f01cbc01e39f6d052d460395c8877dd43eb5d3444ff0999ed10a75a4c33c7cf5
%global app_dir /opt/ZenNotes
%global debug_package %{nil}

Name:           zennotes
Version:        2.2.0
Release:        1%{?dist}
Summary:        Markdown notes app with local-first vaults

License:        MIT
URL:            https://github.com/ZenNotes/zennotes
Source0:        https://github.com/ZenNotes/zennotes/releases/download/v%{version}/%{upstream_deb}
Source1:        https://raw.githubusercontent.com/ZenNotes/zennotes/v%{version}/LICENSE

ExclusiveArch:  x86_64

BuildRequires:  binutils
BuildRequires:  coreutils
BuildRequires:  desktop-file-utils
BuildRequires:  findutils
BuildRequires:  gzip
BuildRequires:  shared-mime-info
BuildRequires:  tar
BuildRequires:  xz
BuildRequires:  zstd

Requires:       at-spi2-core
Requires:       gtk3
Requires:       libnotify
Requires:       libsecret
Requires:       libuuid
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       nss
Requires:       xdg-utils
Requires(post): desktop-file-utils
Requires(post): gtk-update-icon-cache
Requires(post): shared-mime-info
Requires(postun): desktop-file-utils
Requires(postun): gtk-update-icon-cache
Requires(postun): shared-mime-info
Recommends:     libappindicator-gtk3

%description
ZenNotes is a local-first Markdown notes app with desktop, CLI, and MCP support.

This COPR package republishes the official upstream GitHub Release DEB so
Fedora can install and update ZenNotes through normal DNF/COPR metadata. It does
not rebuild ZenNotes from source.

%prep
%setup -q -c -T

actual_sum="$(sha256sum %{SOURCE0} | awk '{ print $1 }')"
if [ "%{upstream_deb_sha256}" != "$actual_sum" ]; then
    echo "ERROR: checksum verification failed for %{upstream_deb}" >&2
    echo "Expected: %{upstream_deb_sha256}" >&2
    echo "Actual:   $actual_sum" >&2
    exit 1
fi

mkdir payload deb-control
ar x %{SOURCE0}

control_archive="$(find . -maxdepth 1 -type f -name 'control.tar.*' -print -quit)"
data_archive="$(find . -maxdepth 1 -type f -name 'data.tar.*' -print -quit)"
if [ -z "$control_archive" ] || [ -z "$data_archive" ]; then
    echo "ERROR: expected control.tar.* and data.tar.* in %{upstream_deb}" >&2
    exit 1
fi

tar -xf "$control_archive" -C deb-control
tar -xf "$data_archive" -C payload

unexpected_path="$(find payload -mindepth 1 -maxdepth 1 ! -name opt ! -name usr -print -quit)"
if [ -n "$unexpected_path" ]; then
    echo "ERROR: unexpected top-level payload path: $unexpected_path" >&2
    exit 1
fi

test -d payload/opt/ZenNotes
test -d payload/usr/share/applications
test -d payload/usr/share/icons/hicolor
test -d payload/usr/share/mime/packages

%build
# Upstream binary DEB repackaging; nothing to build.

%install
mkdir -p %{buildroot}
cp -a payload/opt payload/usr %{buildroot}/

install -D -m 0644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE
mkdir -p %{buildroot}%{_bindir}
ln -s ../../opt/ZenNotes/ZenNotes %{buildroot}%{_bindir}/zennotes
ln -s ../../opt/ZenNotes/resources/zen %{buildroot}%{_bindir}/zen

# Upstream Linux update metadata points at GitHub AppImage/DEB assets. COPR/DNF
# should remain the update path for this RPM package.
rm -f %{buildroot}%{app_dir}/resources/app-update.yml
rm -f %{buildroot}%{app_dir}/resources/package-type

sed -i 's/text\/markdown;text\/markdown;/text\/markdown;/' \
    %{buildroot}%{_datadir}/applications/ZenNotes.desktop
chmod 4755 %{buildroot}%{app_dir}/chrome-sandbox

%check
test -x %{buildroot}%{app_dir}/ZenNotes
test -x %{buildroot}%{app_dir}/resources/zen
test -f %{buildroot}%{app_dir}/resources/cli.js
test ! -f %{buildroot}%{app_dir}/resources/app-update.yml
test ! -f %{buildroot}%{app_dir}/resources/package-type
test -L %{buildroot}%{_bindir}/zennotes
test -L %{buildroot}%{_bindir}/zen
test -x %{buildroot}%{_bindir}/zennotes
test -x %{buildroot}%{_bindir}/zen
desktop-file-validate %{buildroot}%{_datadir}/applications/ZenNotes.desktop
mkdir -p mime-check/mime
cp -a %{buildroot}%{_datadir}/mime/packages mime-check/mime/
XDG_DATA_HOME="$PWD/mime-check" update-mime-database -n mime-check/mime

%post
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor || :
update-desktop-database -q %{_datadir}/applications || :
update-mime-database -n %{_datadir}/mime || :

%postun
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor || :
update-desktop-database -q %{_datadir}/applications || :
update-mime-database -n %{_datadir}/mime || :

%files
%license %{_licensedir}/%{name}/LICENSE
%doc %{_docdir}/%{name}/changelog.gz
%{_bindir}/zennotes
%{_bindir}/zen
%{_datadir}/applications/ZenNotes.desktop
%{_datadir}/icons/hicolor/*/apps/ZenNotes.png
%{_datadir}/mime/packages/ZenNotes.xml
%dir %{app_dir}
%{app_dir}/chrome_100_percent.pak
%{app_dir}/chrome_200_percent.pak
%{app_dir}/chrome_crashpad_handler
%attr(4755,root,root) %{app_dir}/chrome-sandbox
%{app_dir}/icudtl.dat
%{app_dir}/libEGL.so
%{app_dir}/libffmpeg.so
%{app_dir}/libGLESv2.so
%{app_dir}/libvk_swiftshader.so
%{app_dir}/libvulkan.so.1
%{app_dir}/LICENSE.electron.txt
%{app_dir}/LICENSES.chromium.html
%{app_dir}/locales
%{app_dir}/resources
%{app_dir}/resources.pak
%{app_dir}/snapshot_blob.bin
%{app_dir}/v8_context_snapshot.bin
%{app_dir}/vk_swiftshader_icd.json
%{app_dir}/ZenNotes

%changelog
%autochangelog

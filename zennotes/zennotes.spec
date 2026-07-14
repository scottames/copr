%global upstream_rpm ZenNotes-%{version}-linux-x86_64.rpm
%global upstream_rpm_sha256 e24be603b4221563cd4ea6276ce7bf35f87efef07bf52076728a7e2e70af5684
%global app_dir %{_libdir}/%{name}
%global debug_package %{nil}

Name:           zennotes
Version:        2.13.2
Release:        2%{?dist}
Summary:        Markdown notes app with local-first vaults

License:        MIT
URL:            https://github.com/ZenNotes/zennotes
Source0:        https://github.com/ZenNotes/zennotes/releases/download/v%{version}/%{upstream_rpm}
Source1:        https://raw.githubusercontent.com/ZenNotes/zennotes/v%{version}/LICENSE

ExclusiveArch:  x86_64

BuildRequires:  coreutils
BuildRequires:  bsdtar
BuildRequires:  desktop-file-utils
BuildRequires:  findutils
BuildRequires:  gawk
BuildRequires:  rpm
BuildRequires:  shared-mime-info

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

This COPR package republishes the official upstream GitHub Release RPM so
Fedora can install and update ZenNotes through normal DNF/COPR metadata. It does
not rebuild ZenNotes from source.

%prep
%setup -q -c -T

actual_sum="$(sha256sum %{SOURCE0} | awk '{ print $1 }')"
if [ "%{upstream_rpm_sha256}" != "$actual_sum" ]; then
    echo "ERROR: checksum verification failed for %{upstream_rpm}" >&2
    echo "Expected: %{upstream_rpm_sha256}" >&2
    echo "Actual:   $actual_sum" >&2
    exit 1
fi

test "$(rpm -qp --qf '%%{NAME}' %{SOURCE0})" = "ZenNotes"
test "$(rpm -qp --qf '%%{VERSION}' %{SOURCE0})" = "%{version}"
test "$(rpm -qp --qf '%%{ARCH}' %{SOURCE0})" = "x86_64"
rpmkeys --checksig %{SOURCE0}

unexpected_rpm_entry="$(rpm -qp --qf '[%%{FILEMODES:octal}\t%%{FILENAMES}\n]' %{SOURCE0} | awk '
    $1 ~ /^10[0-7]{4}$/ || $1 ~ /^4[0-7]{4}$/ { next }
    $1 ~ /^12[0-7]{4}$/ && $2 ~ /^\/usr\/lib\/\.build-id\/[0-9a-f]{2}\/[0-9a-f]+$/ { next }
    { print $2; exit }
')"
if [ -n "$unexpected_rpm_entry" ]; then
    echo "ERROR: unsafe upstream RPM entry: $unexpected_rpm_entry" >&2
    exit 1
fi

mkdir payload
rpm2cpio %{SOURCE0} | bsdtar -xf - -C payload \
    --no-same-owner --no-same-permissions \
    --exclude './usr/lib/.build-id*' --exclude 'usr/lib/.build-id*'

unexpected_path="$(find payload -mindepth 1 -maxdepth 1 ! -name opt ! -name usr -print -quit)"
if [ -n "$unexpected_path" ]; then
    echo "ERROR: unexpected top-level payload path: $unexpected_path" >&2
    exit 1
fi

test -d payload/opt/ZenNotes
test ! -L payload/opt/ZenNotes
test -d payload/usr/share/applications
test -d payload/usr/share/icons/hicolor
test -d payload/usr/share/mime/packages
test -f payload/usr/share/applications/ZenNotes.desktop
test -f payload/usr/share/mime/packages/ZenNotes.xml

unexpected_opt_path="$(find payload/opt -mindepth 1 -maxdepth 1 ! -name ZenNotes -print -quit)"
if [ -n "$unexpected_opt_path" ]; then
    echo "ERROR: unexpected upstream /opt path: $unexpected_opt_path" >&2
    exit 1
fi

unexpected_usr_path="$(find payload/usr -mindepth 1 -maxdepth 1 ! -name share -print -quit)"
if [ -n "$unexpected_usr_path" ]; then
    echo "ERROR: unexpected upstream /usr path: $unexpected_usr_path" >&2
    exit 1
fi

unexpected_share_path="$(find payload/usr/share -mindepth 1 -maxdepth 1 \
    ! -name applications ! -name icons ! -name mime -print -quit)"
if [ -n "$unexpected_share_path" ]; then
    echo "ERROR: unexpected upstream /usr/share path: $unexpected_share_path" >&2
    exit 1
fi

unexpected_application="$(find payload/usr/share/applications -mindepth 1 \
    ! -name ZenNotes.desktop -print -quit)"
unexpected_mime="$(find payload/usr/share/mime/packages -mindepth 1 \
    ! -name ZenNotes.xml -print -quit)"
if [ -n "$unexpected_application" ] || [ -n "$unexpected_mime" ]; then
    echo "ERROR: unexpected upstream desktop or MIME payload" >&2
    exit 1
fi

icon_entry_count="$(find payload/usr/share/icons/hicolor -mindepth 1 -printf x | wc -c)"
test "$icon_entry_count" -eq 24
for size in 16 24 32 48 64 128 256 512; do
    icon_dir="payload/usr/share/icons/hicolor/${size}x${size}"
    test -d "$icon_dir"
    test ! -L "$icon_dir"
    test -d "$icon_dir/apps"
    test ! -L "$icon_dir/apps"
    test -f "$icon_dir/apps/ZenNotes.png"
    test ! -L "$icon_dir/apps/ZenNotes.png"
done

%build
# Upstream binary RPM repackaging; nothing to build.

%install
mkdir -p %{buildroot}

# Upstream's RPM installs the Electron app under /opt/ZenNotes. On Fedora
# Atomic/rpm-ostree systems /opt is a mutable /var/opt location, so RPM-owned
# application payloads should live under /usr instead. Keep the upstream
# payload contents intact, but relocate them into Fedora's private libdir and
# patch the launchers below to avoid owning or depending on /opt.
install -D -m 0644 payload/usr/share/applications/ZenNotes.desktop \
    %{buildroot}%{_datadir}/applications/ZenNotes.desktop
install -D -m 0644 payload/usr/share/mime/packages/ZenNotes.xml \
    %{buildroot}%{_datadir}/mime/packages/ZenNotes.xml
for size in 16 24 32 48 64 128 256 512; do
    install -D -m 0644 \
        "payload/usr/share/icons/hicolor/${size}x${size}/apps/ZenNotes.png" \
        "%{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/ZenNotes.png"
done
install -d %{buildroot}%{app_dir}
cp -a payload/opt/ZenNotes/. %{buildroot}%{app_dir}/

install -D -m 0644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE
mkdir -p %{buildroot}%{_bindir}
ln -s ../%{_lib}/%{name}/ZenNotes %{buildroot}%{_bindir}/zennotes

# Upstream Linux update metadata points at GitHub AppImage/DEB assets. COPR/DNF
# should remain the update path for this RPM package.
rm -f %{buildroot}%{app_dir}/LICENSE
rm -f %{buildroot}%{app_dir}/resources/app-update.yml
rm -f %{buildroot}%{app_dir}/resources/package-type

sed -i \
    -e 's|Exec=/opt/ZenNotes/ZenNotes %U|Exec=%{app_dir}/ZenNotes %U|' \
    -e 's/text\/markdown;text\/markdown;/text\/markdown;/' \
    %{buildroot}%{_datadir}/applications/ZenNotes.desktop
chmod 4755 %{buildroot}%{app_dir}/chrome-sandbox

%check
test -x %{buildroot}%{app_dir}/ZenNotes
test -x %{buildroot}%{app_dir}/resources/zen
test -f %{buildroot}%{app_dir}/resources/cli.js
test ! -f %{buildroot}%{app_dir}/resources/app-update.yml
test ! -f %{buildroot}%{app_dir}/resources/package-type
test -L %{buildroot}%{_bindir}/zennotes
test "$(readlink %{buildroot}%{_bindir}/zennotes)" = "../%{_lib}/%{name}/ZenNotes"
test -x %{buildroot}%{_bindir}/zennotes
test ! -e %{buildroot}%{_bindir}/zen
test ! -e %{buildroot}%{_bindir}/zn
test ! -e %{buildroot}/opt
test -z "$(find %{buildroot} -path '*/.build-id/*' -print -quit)"
grep -qx 'Exec=%{app_dir}/ZenNotes %U' \
    %{buildroot}%{_datadir}/applications/ZenNotes.desktop
! grep -q '/opt/ZenNotes' %{buildroot}%{_datadir}/applications/ZenNotes.desktop
privileged_files="$(find %{buildroot} -perm /6000 -printf '%%p\n')"
expected_privileged_file="%{buildroot}%{app_dir}/chrome-sandbox"
if [ "$privileged_files" != "$expected_privileged_file" ]; then
    echo "ERROR: unexpected setuid/setgid files in %{app_dir}" >&2
    printf 'Expected:\n%s\nActual:\n%s\n' "$expected_privileged_file" "$privileged_files" >&2
    exit 1
fi
test "$(stat -c '%%a' %{buildroot}%{app_dir}/chrome-sandbox)" = 4755
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
%{_bindir}/zennotes
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

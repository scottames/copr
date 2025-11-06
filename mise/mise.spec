%global debug_package %{nil}

# Map RPM architecture to mise's naming convention
%ifarch x86_64
%global mise_arch x64
%endif
%ifarch aarch64
%global mise_arch arm64
%endif

Name:           mise
Version:        2025.11.2
Release:        1%{?dist}
Summary:        The front-end to your dev env

License:        MIT
URL:            https://mise.jdx.dev
# Source tarball for documentation and LICENSE files
Source0:        https://github.com/jdx/mise/archive/v%{version}/mise-%{version}.tar.gz
# Prebuilt binary tarball - architecture specific
Source1:        https://github.com/jdx/mise/releases/download/v%{version}/mise-v%{version}-linux-%{mise_arch}.tar.xz
# Checksum file for verification
Source2:        https://github.com/jdx/mise/releases/download/v%{version}/SHASUMS256.txt

# No build requirements needed since we're using prebuilt binaries

%description
mise is a development environment setup tool that manages runtime versions,
environment variables, and tasks. It's a replacement for tools like nvm, rbenv,
pyenv, etc. and works with any language.

%prep
# Verify checksum of binary tarball before extraction
EXPECTED_SUM=$(grep "mise-v%{version}-linux-%{mise_arch}.tar.xz" %{SOURCE2} | cut -d' ' -f1)
ACTUAL_SUM=$(sha256sum %{SOURCE1} | cut -d' ' -f1)
if [ "$EXPECTED_SUM" != "$ACTUAL_SUM" ]; then
    echo "ERROR: Checksum verification failed for mise-v%{version}-linux-%{mise_arch}.tar.xz"
    echo "Expected: $EXPECTED_SUM"
    echo "Actual:   $ACTUAL_SUM"
    exit 1
fi
echo "Checksum verified successfully: $ACTUAL_SUM"

# Extract source tarball for docs/license
%autosetup -n %{name}-%{version}

# Extract prebuilt binary tarball
tar -xf %{SOURCE1} --strip-components=1 -C .

%build
# No build needed - using prebuilt binaries

%install
# Install binary
mkdir -p %{buildroot}%{_bindir}
install -m 0755 bin/mise %{buildroot}%{_bindir}/mise

# Install man page
mkdir -p %{buildroot}%{_mandir}/man1
install -m 0644 man/man1/mise.1 %{buildroot}%{_mandir}/man1/

# Generate and install shell completions using the mise binary itself
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
%{buildroot}%{_bindir}/mise completion bash > %{buildroot}%{_datadir}/bash-completion/completions/mise

mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
%{buildroot}%{_bindir}/mise completion zsh > %{buildroot}%{_datadir}/zsh/site-functions/_mise

mkdir -p %{buildroot}%{_datadir}/fish/vendor_completions.d
%{buildroot}%{_bindir}/mise completion fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/mise.fish

# Disable self-update for package manager installations
mkdir -p %{buildroot}%{_libdir}/mise
cat > %{buildroot}%{_libdir}/mise/mise-self-update-instructions.toml <<'TOML'
message = "To update mise from COPR, run:\n\n  sudo dnf upgrade mise\n"
TOML

%files
%license LICENSE
%doc README.md
%{_bindir}/mise
%{_mandir}/man1/mise.1*
%{_datadir}/bash-completion/completions/mise
%{_datadir}/zsh/site-functions/_mise
%{_datadir}/fish/vendor_completions.d/mise.fish
%{_libdir}/mise/mise-self-update-instructions.toml

%changelog
%autochangelog

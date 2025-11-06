%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           mise
Version:        2025.11.2
Release:        1%{?dist}
Summary:        The front-end to your dev env

License:        MIT
URL:            https://mise.jdx.dev
Source0:        https://github.com/jdx/mise/archive/v%{version}/mise-%{version}.tar.gz
Source1:        mise-vendor-%{version}.tar.gz

BuildRequires:  rust >= 1.85
BuildRequires:  cargo
BuildRequires:  gcc
BuildRequires:  git
BuildRequires:  openssl-devel

%description
mise is a development environment setup tool that manages runtime versions,
environment variables, and tasks. It's a replacement for tools like nvm, rbenv,
pyenv, etc. and works with any language.

%prep
%autosetup -n %{name}-%{version}
%setup -q -T -D -a 1

%build
# Set up vendored dependencies
mkdir -p .cargo
cp .cargo/config.toml .cargo/config.toml.bak 2>/dev/null || true
cat > .cargo/config.toml << 'CARGO_EOF'
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "vendor"
CARGO_EOF

# Build with specified profile
cargo build --profile release --frozen --bin mise

%install
mkdir -p %{buildroot}%{_bindir}
cp target/release/mise %{buildroot}%{_bindir}/

# Install man page if available
mkdir -p %{buildroot}%{_mandir}/man1
cp man/man1/mise.1 %{buildroot}%{_mandir}/man1/

# Install shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
cp completions/mise.bash %{buildroot}%{_datadir}/bash-completion/completions/mise

mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
cp completions/_mise %{buildroot}%{_datadir}/zsh/site-functions/

mkdir -p %{buildroot}%{_datadir}/fish/vendor_completions.d
cp completions/mise.fish %{buildroot}%{_datadir}/fish/vendor_completions.d/

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

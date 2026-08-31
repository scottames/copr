%global upstream_release 1
%global upstream_rpm %{name}-%{version}-%{upstream_release}.x86_64.rpm
%global upstream_rpm_sha256 341e2767948ed4045158860600ec1a9727ceadca6b7da7edf22322d76238119b
%global debug_package %{nil}

Name:           voxtype
Version:        1.0.0
Release:        1%{?dist}
Summary:        Push-to-talk voice-to-text for Linux

License:        MIT
URL:            https://voxtype.io
Source0:        https://github.com/peteonrails/voxtype/releases/download/v%{version}/%{upstream_rpm}

ExclusiveArch:  x86_64
AutoReqProv:    no

BuildRequires:  coreutils
BuildRequires:  cpio
BuildRequires:  findutils
BuildRequires:  gawk
BuildRequires:  patchelf
BuildRequires:  rpm
BuildRequires:  systemd-rpm-macros

Requires:       alsa-lib
Requires:       curl
Requires:       glibc
Requires:       gtk4
Requires:       gtk4-layer-shell
Requires:       pipewire-alsa

%description
Voxtype is a push-to-talk voice-to-text tool for Linux.

This COPR package republishes the official upstream GitHub Release RPM so
Fedora can install and update Voxtype through normal DNF/COPR metadata. It does
not rebuild Voxtype from source.

%prep
%setup -q -c -T

actual_sum="$(sha256sum %{SOURCE0} | awk '{ print $1 }')"
if [ "%{upstream_rpm_sha256}" != "$actual_sum" ]; then
    echo "ERROR: checksum verification failed for %{upstream_rpm}" >&2
    echo "Expected: %{upstream_rpm_sha256}" >&2
    echo "Actual:   $actual_sum" >&2
    exit 1
fi

mkdir payload
cd payload
rpm2cpio %{SOURCE0} | cpio -idm --quiet

unexpected_path="$(find . -mindepth 1 -maxdepth 1 ! -name etc ! -name usr -print -quit)"
if [ -n "$unexpected_path" ]; then
    echo "ERROR: unexpected top-level payload path: $unexpected_path" >&2
    exit 1
fi

test -d etc
test -d usr

%build
# Upstream binary RPM repackaging; nothing to build.

%install
mkdir -p %{buildroot}
cp -a payload/etc payload/usr %{buildroot}/

# Upstream's ONNX provider libraries include build-host/toolchain RUNPATHs
# that Fedora RPM policy rejects. Remove them rather than disabling RPATH QA
# globally; runtime CUDA/ROCm discovery should come from the host linker setup.
patchelf --remove-rpath %{buildroot}%{_prefix}/lib/voxtype/cuda-12/libonnxruntime_providers_cuda.so
patchelf --remove-rpath %{buildroot}%{_prefix}/lib/voxtype/cuda-13/libonnxruntime_providers_cuda.so
patchelf --remove-rpath %{buildroot}%{_prefix}/lib/voxtype/migraphx/libonnxruntime_providers_migraphx.so

%check
test -f payload/etc/voxtype/config.toml
test -x payload/usr/bin/voxtype
test -x payload/usr/bin/voxtype-audio-bridge
test -L payload/usr/bin/voxtype-osd
test -f payload/usr/lib/systemd/user/voxtype.service
test -x payload/usr/lib/voxtype/voxtype-osd
test -x payload/usr/lib/voxtype/voxtype-osd-gtk4
test -x payload/usr/lib/voxtype/voxtype-osd-quickshell
test -f payload/usr/share/voxtype/quickshell/shell.qml

%post
#!/bin/sh
# Voxtype post-installation script
#
# Binary variants (x86_64):
#   voxtype-avx2:   CPU - Works on most CPUs from 2013+ (Intel Haswell, AMD Zen)
#   voxtype-avx512: CPU - Optimized for newer CPUs (AMD Zen 4+, some Intel)
#   voxtype-vulkan: GPU - Vulkan acceleration (NVIDIA, AMD, Intel)
#
# The /usr/bin/voxtype wrapper automatically selects the best binary for your CPU.

# Restore SELinux context if available (for Fedora/RHEL)
if command -v restorecon >/dev/null 2>&1; then
    restorecon /usr/bin/voxtype 2>/dev/null || true
fi

# Detect CPU variant that will be used
VARIANT="avx2"
if [ -f /proc/cpuinfo ] && grep -q avx512f /proc/cpuinfo 2>/dev/null; then
    VARIANT="avx512"
fi

# Detect GPU for Vulkan acceleration recommendation
GPU_DETECTED=""
if [ -d /dev/dri ]; then
    # Check for render nodes (indicates GPU with driver)
    if ls /dev/dri/renderD* >/dev/null 2>&1; then
        # Try to identify the GPU
        if command -v lspci >/dev/null 2>&1; then
            GPU_INFO=$(lspci 2>/dev/null | grep -i 'vga\|3d\|display' | head -1 | sed 's/.*: //')
            if [ -n "$GPU_INFO" ]; then
                GPU_DETECTED="$GPU_INFO"
            fi
        fi
        # Fallback if lspci didn't work
        if [ -z "$GPU_DETECTED" ]; then
            GPU_DETECTED="GPU detected (install pciutils for details)"
        fi
    fi
fi

echo ""
echo "=== Voxtype Post-Installation ==="
echo ""
echo "CPU backend: $VARIANT (auto-detected)"

if [ -n "$GPU_DETECTED" ]; then
    echo ""
    echo "GPU detected: $GPU_DETECTED"
    echo ""
    echo "  For GPU acceleration (faster inference), run:"
    echo "    sudo voxtype setup gpu --enable"
    echo ""
    echo "  Requires: vulkan-loader and GPU drivers"
fi

echo ""
echo "To complete setup:"
echo ""
echo "  1. Download a model (Whisper or Parakeet):"
echo "     voxtype setup model"
echo ""
echo "  2. Start voxtype:"
echo "     systemctl --user enable --now voxtype"
echo ""
echo "  Optional: For the built-in evdev hotkey, add your user to the"
echo "  'input' group, then log out and back in. Compositor keybindings"
echo "  do not require this access:"
echo "     sudo usermod -aG input \$USER"
echo ""
echo "  Optional: Switch to Parakeet engine (faster, lower memory):"
echo "     voxtype setup parakeet --enable"
echo ""

%postun
#!/bin/sh
# Voxtype post-uninstall script
# Nothing to do - wrapper script is removed with package

%files
%config(noreplace) %{_sysconfdir}/voxtype/config.toml
%{_bindir}/voxtype
%{_bindir}/voxtype-audio-bridge
%{_bindir}/voxtype-osd
%dir %{_prefix}/lib/.build-id
%dir %{_prefix}/lib/.build-id/*
%{_prefix}/lib/.build-id/*/*
%{_userunitdir}/voxtype.service
%dir %{_prefix}/lib/voxtype
%dir %{_prefix}/lib/voxtype/cuda-12
%{_prefix}/lib/voxtype/cuda-12/libonnxruntime_providers_cuda.so
%{_prefix}/lib/voxtype/cuda-12/libonnxruntime_providers_shared.so
%{_prefix}/lib/voxtype/cuda-12/voxtype-onnx-cuda-12
%dir %{_prefix}/lib/voxtype/cuda-13
%{_prefix}/lib/voxtype/cuda-13/libonnxruntime.so*
%{_prefix}/lib/voxtype/cuda-13/libonnxruntime_providers_cuda.so
%{_prefix}/lib/voxtype/cuda-13/libonnxruntime_providers_shared.so
%{_prefix}/lib/voxtype/cuda-13/voxtype-onnx-cuda-13
%dir %{_prefix}/lib/voxtype/migraphx
%{_prefix}/lib/voxtype/migraphx/libonnxruntime_providers_migraphx.so
%{_prefix}/lib/voxtype/migraphx/libonnxruntime_providers_shared.so
%{_prefix}/lib/voxtype/migraphx/voxtype-onnx-migraphx
%{_prefix}/lib/voxtype/voxtype-avx2
%{_prefix}/lib/voxtype/voxtype-avx512
%{_prefix}/lib/voxtype/voxtype-onnx-avx2
%{_prefix}/lib/voxtype/voxtype-onnx-avx512
%{_prefix}/lib/voxtype/voxtype-onnx-cuda-12
%{_prefix}/lib/voxtype/voxtype-onnx-cuda-13
%{_prefix}/lib/voxtype/voxtype-onnx-migraphx
%{_prefix}/lib/voxtype/voxtype-onnx-rocm
%{_prefix}/lib/voxtype/voxtype-osd
%{_prefix}/lib/voxtype/voxtype-osd-gtk4
%{_prefix}/lib/voxtype/voxtype-osd-quickshell
%{_prefix}/lib/voxtype/voxtype-vulkan
%{_datadir}/bash-completion/completions/voxtype
%license %{_docdir}/voxtype/LICENSE
%doc %{_docdir}/voxtype/README.md
%{_datadir}/fish/vendor_completions.d/voxtype.fish
%{_datadir}/voxtype
%{_datadir}/zsh/site-functions/_voxtype

%changelog
%autochangelog

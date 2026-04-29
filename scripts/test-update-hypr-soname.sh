#!/usr/bin/env bash
# Scenario snippets invoke helper functions and variables through eval.
# shellcheck disable=SC2016,SC2034,SC2329
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
HELPER_SCRIPT="$SCRIPT_DIR/update-hypr-soname.sh"

failures=0

run_case() {
    local name=$1
    local setup=$2
    local expected_status=${3:-0}

    local tmpdir
    tmpdir=$(mktemp -d)
    trap 'rm -rf "$tmpdir"' RETURN

    local status=0
    local output
    pushd "$tmpdir" >/dev/null
    mkdir -p hypr fixtures
    output=$(eval "$setup" 2>&1) || status=$?
    popd >/dev/null

    if [ "$status" -eq "$expected_status" ]; then
        printf 'ok - %s\n' "$name"
    else
        printf 'not ok - %s\n' "$name"
        printf 'expected status %s, got %s\n' "$expected_status" "$status"
        printf '%s\n' "$output"
        failures=$((failures + 1))
    fi
}

write_spec() {
    local name=$1
    local version=$2
    local soname=$3
    local libname=${4:-'%{name}'}

    cat > "hypr/$name.spec" <<EOF
Name:           $name
Version:        $version
Release:        %autorelease
Summary:        Test package
License:        MIT
URL:            https://github.com/hyprwm/$name
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

%description
Test package.

%files
%{_libdir}/lib%{name}.so.%{version}
%{_libdir}/lib$libname.so.$soname
EOF
}

write_spec_with_extra_library() {
    local name=$1
    local version=$2
    local soname=$3

    write_spec "$name" "$version" "$soname"
    sed -i '/%{_libdir}\/lib%{name}.so.%{version}/i %{_libdir}/libother.so.1' "hypr/$name.spec"
}

write_spec_with_commented_soname() {
    local name=$1
    local version=$2
    local soname=$3

    write_spec "$name" "$version" "$soname"
    sed -i '/%{_libdir}\/lib%{name}.so.%{version}/i # %{_libdir}/lib%{name}.so.1' "hypr/$name.spec"
}

write_spec_without_soname() {
    local name=$1
    local version=$2

    cat > "hypr/$name.spec" <<EOF
Name:           $name
Version:        $version
Release:        %autorelease
Summary:        Test package
License:        MIT
URL:            https://github.com/hyprwm/$name
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

%description
Test package.

%files
%{_bindir}/$name
EOF
}

write_spec_without_version() {
    local name=$1

    cat > "hypr/$name.spec" <<EOF
Name:           $name
Release:        %autorelease
Summary:        Test package
License:        MIT
URL:            https://github.com/hyprwm/$name

%description
Test package.

%files
%{_libdir}/lib%{name}.so.1
EOF
}

write_cmake() {
    local name=$1
    local version=$2
    local soversion=$3

    mkdir -p "fixtures/$name/v$version"
    cat > "fixtures/$name/v$version/CMakeLists.txt" <<EOF
add_library($name SHARED src/main.cpp)
set_target_properties($name PROPERTIES VERSION \${${name}_VERSION}
                                       SOVERSION $soversion)
EOF
}

write_cmake_without_soversion() {
    local name=$1
    local version=$2

    mkdir -p "fixtures/$name/v$version"
    cat > "fixtures/$name/v$version/CMakeLists.txt" <<EOF
add_library($name SHARED src/main.cpp)
set_target_properties($name PROPERTIES VERSION \${${name}_VERSION})
EOF
}

write_cmake_split_soversion() {
    local name=$1
    local version=$2
    local soversion=$3

    mkdir -p "fixtures/$name/v$version"
    cat > "fixtures/$name/v$version/CMakeLists.txt" <<EOF
add_library($name SHARED src/main.cpp)
set_target_properties($name PROPERTIES VERSION \${${name}_VERSION} SOVERSION
                                      $soversion)
EOF
}

run_case \
    'report mode detects mismatched hypr soname' \
    'write_spec hyprutils 0.13.0 11 && write_cmake hyprutils 0.13.0 12 && set +e; helper_output=$(HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" hypr/hyprutils.spec 2>&1); helper_status=$?; set -e; [ "$helper_status" -eq 1 ] && grep -q "libhyprutils.so.11 -> libhyprutils.so.12" <<< "$helper_output"'

run_case \
    'report mode allows matching hypr soname' \
    'write_spec aquamarine 0.11.0 10 && write_cmake aquamarine 0.11.0 10 && HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" hypr/aquamarine.spec | grep -q "libaquamarine.so.10 is current"'

run_case \
    'report mode handles explicit hyprlang library name' \
    'write_spec hyprlang 0.6.8 1 hyprlang && write_cmake hyprlang 0.6.8 2 && set +e; helper_output=$(HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" hypr/hyprlang.spec 2>&1); helper_status=$?; set -e; [ "$helper_status" -eq 1 ] && grep -q "libhyprlang.so.1 -> libhyprlang.so.2" <<< "$helper_output"'

run_case \
    '--apply updates mismatched hypr soname' \
    'write_spec hyprutils 0.13.0 11 && write_cmake hyprutils 0.13.0 12 && HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" --apply hypr/hyprutils.spec && grep -q "%{_libdir}/lib%{name}.so.12" hypr/hyprutils.spec && ! grep -q "%{_libdir}/lib%{name}.so.11" hypr/hyprutils.spec'

run_case \
    'reports missing upstream soversion' \
    'write_spec hyprutils 0.13.0 11 && write_cmake_without_soversion hyprutils 0.13.0 && set +e; helper_output=$(HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" hypr/hyprutils.spec 2>&1); helper_status=$?; set -e; [ "$helper_status" -eq 1 ] && grep -q "could not determine upstream SOVERSION" <<< "$helper_output"'

run_case \
    'report mode handles split cmake soversion value' \
    'write_spec hyprwire 0.3.1 3 && write_cmake_split_soversion hyprwire 0.3.1 3 && HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" hypr/hyprwire.spec | grep -q "libhyprwire.so.3 is current"'

run_case \
    '--apply updates matching package soname when another library appears first' \
    'write_spec_with_extra_library hyprutils 0.13.0 11 && write_cmake hyprutils 0.13.0 12 && HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" --apply hypr/hyprutils.spec && grep -q "%{_libdir}/libother.so.1" hypr/hyprutils.spec && grep -q "%{_libdir}/lib%{name}.so.12" hypr/hyprutils.spec && ! grep -q "%{_libdir}/lib%{name}.so.11" hypr/hyprutils.spec'

run_case \
    'skips specs without hardcoded runtime soname' \
    'write_spec_without_soname hyprlock 0.9.5 && HYPR_SONAME_CMAKE_DIR=missing-fixtures "$HELPER_SCRIPT" hypr/hyprlock.spec | grep -q "skipped: no hardcoded runtime SONAME entry"'

run_case \
    '--apply ignores commented soname lines' \
    'write_spec_with_commented_soname hyprutils 0.13.0 11 && write_cmake hyprutils 0.13.0 12 && HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" --apply hypr/hyprutils.spec && grep -q "# %{_libdir}/lib%{name}.so.1" hypr/hyprutils.spec && grep -q "%{_libdir}/lib%{name}.so.12" hypr/hyprutils.spec && ! grep -q "%{_libdir}/lib%{name}.so.11" hypr/hyprutils.spec'

run_case \
    'missing spec reports error without aborting batch' \
    'write_spec aquamarine 0.11.0 10 && write_cmake aquamarine 0.11.0 10 && set +e; helper_output=$(HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" hypr/missing.spec hypr/aquamarine.spec 2>&1); helper_status=$?; set -e; [ "$helper_status" -eq 1 ] && grep -q "hypr/missing.spec: spec file is not readable" <<< "$helper_output" && grep -q "hypr/aquamarine.spec: libaquamarine.so.10 is current" <<< "$helper_output"'

run_case \
    'missing upstream cmake reports read failure without aborting batch' \
    'write_spec hyprutils 0.13.0 11 && write_spec aquamarine 0.11.0 10 && write_cmake aquamarine 0.11.0 10 && set +e; helper_output=$(HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" hypr/hyprutils.spec hypr/aquamarine.spec 2>&1); helper_status=$?; set -e; [ "$helper_status" -eq 1 ] && grep -q "missing fixture CMakeLists.txt: fixtures/hyprutils/v0.13.0/CMakeLists.txt" <<< "$helper_output" && grep -q "hypr/hyprutils.spec: could not read upstream CMakeLists.txt" <<< "$helper_output" && grep -q "hypr/aquamarine.spec: libaquamarine.so.10 is current" <<< "$helper_output"'

run_case \
    'malformed spec reports missing name or version' \
    'write_spec_without_version hyprutils && set +e; helper_output=$(HYPR_SONAME_CMAKE_DIR=fixtures "$HELPER_SCRIPT" hypr/hyprutils.spec 2>&1); helper_status=$?; set -e; [ "$helper_status" -eq 1 ] && grep -q "could not determine Name and Version" <<< "$helper_output"'

exit "$failures"

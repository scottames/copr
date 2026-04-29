#!/usr/bin/env bash
set -euo pipefail

failures=0
apply=false

usage() {
    printf 'Usage: %s [--apply] SPEC...\n' "${0##*/}"
}

extract_field() {
    local field=$1
    local file=$2

    awk -v field="$field" '
        $1 == field ":" {
            sub("^[^:]+:[[:space:]]*", "")
            print
            exit
        }
    ' "$file"
}

cmake_contents() {
    local name=$1
    local version=$2
    local local_cmake

    if [ -n "${HYPR_SONAME_CMAKE_DIR:-}" ]; then
        local_cmake="$HYPR_SONAME_CMAKE_DIR/$name/v$version/CMakeLists.txt"
        if [ ! -f "$local_cmake" ]; then
            printf '%s\n' "missing fixture CMakeLists.txt: $local_cmake" >&2
            return 1
        fi
        awk '{ print }' "$local_cmake"
        return 0
    fi

    curl -fsSL \
        --connect-timeout 10 \
        --max-time 30 \
        --retry 3 \
        --retry-delay 1 \
        --retry-all-errors \
        "https://raw.githubusercontent.com/hyprwm/$name/v$version/CMakeLists.txt"
}

extract_soversion() {
    awk '
        {
            for (i = 1; i <= NF; i++) {
                if (pending == 1 || $i == "SOVERSION") {
                    value = $(i + 1)
                    if (pending == 1) {
                        value = $i
                    }
                    sub(/^[^0-9]*/, "", value)
                    sub(/[^0-9].*$/, "", value)
                    if (value != "") {
                        print value
                        exit
                    }
                    pending = 1
                }
            }
        }
    '
}

current_soname_entry() {
    local name=$1
    local spec=$2

    awk -v name="$name" '
        /^[[:space:]]*%\{_libdir\}\/lib/ && /\.so\.[0-9]+[[:space:]]*$/ {
            line = $0
            gsub(/%\{name\}/, name, line)
            sub(/^.*\//, "", line)
            if (line ~ "^lib" name "\\.so\\.[0-9]+$") {
                print NR ":" line
                exit
            }
        }
    ' "$spec"
}

replace_soname() {
    local spec=$1
    local line_number=$2
    local soversion=$3
    local spec_dir
    local spec_base
    local tmp

    spec_dir=$(dirname -- "$spec")
    spec_base=$(basename -- "$spec")
    tmp=$(mktemp "$spec_dir/.$spec_base.XXXXXX")

    if ! awk -v line_number="$line_number" -v soversion="$soversion" '
        NR == line_number {
            sub(/\.so\.[0-9]+[[:space:]]*$/, ".so." soversion)
        }
        { print }
    ' "$spec" > "$tmp"; then
        rm -f -- "$tmp"
        return 1
    fi

    if ! mv "$tmp" "$spec"; then
        rm -f -- "$tmp"
        return 1
    fi
}

check_spec() {
    local spec=$1
    local name
    local version
    local soversion
    local current
    local current_entry
    local current_line
    local expected
    local cmake

    if [ ! -r "$spec" ]; then
        printf '%s: spec file is not readable\n' "$spec" >&2
        failures=$((failures + 1))
        return 0
    fi

    name=$(extract_field Name "$spec")
    version=$(extract_field Version "$spec")

    if [ -z "$name" ] || [ -z "$version" ]; then
        printf '%s: could not determine Name and Version\n' "$spec" >&2
        failures=$((failures + 1))
        return 0
    fi

    current_entry=$(current_soname_entry "$name" "$spec")
    if [ -z "$current_entry" ]; then
        printf '%s: skipped: no hardcoded runtime SONAME entry\n' "$spec"
        return 0
    fi
    current_line=${current_entry%%:*}
    current=${current_entry#*:}

    if ! cmake=$(cmake_contents "$name" "$version"); then
        printf '%s: could not read upstream CMakeLists.txt\n' "$spec" >&2
        failures=$((failures + 1))
        return 0
    fi

    soversion=$(extract_soversion <<< "$cmake")

    if [ -z "$soversion" ]; then
        printf '%s: could not determine upstream SOVERSION\n' "$spec" >&2
        failures=$((failures + 1))
        return 0
    fi

    expected="lib$name.so.$soversion"

    if [ "$current" != "$expected" ]; then
        printf '%s: %s -> %s\n' "$spec" "$current" "$expected"
        if [ "$apply" = true ]; then
            if ! replace_soname "$spec" "$current_line" "$soversion"; then
                printf '%s: could not update SONAME line\n' "$spec" >&2
                failures=$((failures + 1))
            fi
        else
            failures=$((failures + 1))
        fi
    else
        printf '%s: %s is current\n' "$spec" "$current"
    fi
}

spec_args=()

while [ "$#" -gt 0 ]; do
    case "$1" in
        --apply)
            apply=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --*)
            printf 'Unknown option: %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
        *)
            spec_args+=("$1")
            ;;
    esac
    shift
done

if [ "${#spec_args[@]}" -eq 0 ]; then
    usage >&2
    exit 2
fi

for spec in "${spec_args[@]}"; do
    check_spec "$spec"
done

exit "$failures"

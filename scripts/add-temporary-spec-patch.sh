#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CHECK_SCRIPT="$SCRIPT_DIR/check-spec-guards.sh"

usage() {
    printf 'Usage: %s SPEC PATCH_FILE REMOVE_AFTER_VERSION REASON\n' "${0##*/}"
}

if [ "$#" -ne 4 ]; then
    usage >&2
    exit 2
fi

spec=$1
patch_file=$2
remove_after_version=$3
reason=$4
spec_dir=$(dirname -- "$spec")
patch_dir=$(dirname -- "$patch_file")

if [ ! -f "$spec" ]; then
    printf 'Spec file not found: %s\n' "$spec" >&2
    exit 1
fi

if [ ! -f "$patch_file" ]; then
    printf 'Patch file not found: %s\n' "$patch_file" >&2
    exit 1
fi

if [ "$patch_dir" != "$spec_dir" ]; then
    printf 'Patch file must be in the same directory as the spec: %s\n' "$patch_file" >&2
    exit 1
fi

if [[ "$reason" =~ [[:space:]] ]]; then
    printf 'Reason must not contain whitespace: %s\n' "$reason" >&2
    exit 1
fi

if ! grep -Eq '^[[:space:]]*%autosetup\b.*(^|[[:space:]])-p1([[:space:]]|$)' "$spec"; then
    printf '%s must use %%autosetup -p1 before adding patch files\n' "$spec" >&2
    exit 1
fi

release=$(awk '
    $1 == "Release:" {
        sub("^[^:]+:[[:space:]]*", "")
        print
        exit
    }
' "$spec")

if [[ "$release" == '%autorelease' ]]; then
    new_release='%autorelease -b1'
elif [[ "$release" =~ ^%autorelease[[:space:]]+-b([0-9]+)$ ]]; then
    new_release="%autorelease -b$((BASH_REMATCH[1] + 1))"
else
    printf '%s has unsupported Release value for automatic bump: %s\n' "$spec" "$release" >&2
    exit 1
fi

next_patch_number=$(awk '
    $1 ~ /^Patch[0-9]*:$/ {
        patch = $1
        sub("^Patch", "", patch)
        sub(":$", "", patch)
        if (patch == "") patch = 0
        if (patch > max) max = patch
        found = 1
    }
    END {
        if (found) print max + 1
        else print 0
    }
' "$spec")

insert_after=$(awk '
    $1 ~ /^Patch[0-9]*:$/ { line = NR }
    $1 ~ /^Source[0-9]*:$/ && line == "" { line = NR }
    END { print line }
' "$spec")

if [ -z "$insert_after" ]; then
    printf '%s has no Source or Patch line to insert after\n' "$spec" >&2
    exit 1
fi

patch_basename=$(basename -- "$patch_file")
guard_line="# patch-guard: remove-after-version=$remove_after_version reason=$reason"
patch_line="Patch$next_patch_number:         $patch_basename"

tmp=$(mktemp)
awk -v insert_after="$insert_after" \
    -v guard_line="$guard_line" \
    -v patch_line="$patch_line" \
    -v new_release="$new_release" '
    $1 == "Release:" {
        sub("^[^:]+:[[:space:]]*.*", "Release:        " new_release)
    }
    { print }
    NR == insert_after {
        print guard_line
        print patch_line
    }
' "$spec" > "$tmp"
mv "$tmp" "$spec"

printf '%s: added %s with guard %s\n' "$spec" "$patch_line" "$guard_line"
"$CHECK_SCRIPT"

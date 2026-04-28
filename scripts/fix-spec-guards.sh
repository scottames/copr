#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CHECK_SCRIPT="$SCRIPT_DIR/check-spec-guards.sh"

apply=false
spec_args=()

usage() {
    printf 'Usage: %s [--apply] [spec ...]\n' "${0##*/}"
}

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

base_ref() {
    if [ -n "${SPEC_GUARDS_BASE_REF:-}" ]; then
        printf '%s\n' "$SPEC_GUARDS_BASE_REF"
    elif [ -n "${GITHUB_BASE_REF:-}" ] && git rev-parse --verify --quiet "origin/$GITHUB_BASE_REF" >/dev/null; then
        printf 'origin/%s\n' "$GITHUB_BASE_REF"
    else
        printf 'HEAD\n'
    fi
}

changed_specs() {
    local base=$1

    if [ "${#spec_args[@]}" -gt 0 ]; then
        printf '%s\n' "${spec_args[@]}"
    else
        git diff --name-only "$base" -- '*/*.spec'
    fi
}

rpm_vercmp() {
    local left=$1
    local right=$2

    rpm --eval "%{lua:print(rpm.vercmp('$left', '$right'))}"
}

base_version_for() {
    local base=$1
    local spec=$2
    local base_content

    if ! base_content=$(git show "$base:$spec" 2>/dev/null); then
        return 0
    fi

    awk '
        $1 == "Version:" {
            sub("^[^:]+:[[:space:]]*", "")
            print
            exit
        }
    ' <<< "$base_content"
}

reset_release_value() {
    local release=$1

    if [[ "$release" =~ ^%autorelease([[:space:]]+-b[0-9]+)?$ ]]; then
        printf '%%autorelease\n'
    elif [[ "$release" =~ ^[0-9]+%\{\?dist\}$ ]]; then
        printf '1%%{?dist}\n'
    else
        return 1
    fi
}

replace_release() {
    local spec=$1
    local new_release=$2
    local tmp

    tmp=$(mktemp)
    awk -v new_release="$new_release" '
        $1 == "Release:" {
            sub("^[^:]+:[[:space:]]*.*", "Release:        " new_release)
        }
        { print }
    ' "$spec" > "$tmp"
    mv "$tmp" "$spec"
}

fix_release_if_needed() {
    local base=$1
    local spec=$2
    local base_version
    local current_version
    local current_release
    local new_release

    base_version=$(base_version_for "$base" "$spec")
    current_version=$(extract_field Version "$spec")
    current_release=$(extract_field Release "$spec")

    if [ -z "$base_version" ] || [ "$base_version" = "$current_version" ]; then
        return 0
    fi

    if ! new_release=$(reset_release_value "$current_release"); then
        printf '%s: cannot reset unsupported Release value: %s\n' "$spec" "$current_release" >&2
        return 1
    fi

    printf '%s: reset Release from %s to %s\n' "$spec" "$current_release" "$new_release"
    if [ "$apply" = true ]; then
        replace_release "$spec" "$new_release"
    fi
}

line_is_expired_guard() {
    local line=$1
    local current_version=$2
    local guard_version
    local cmp

    [[ "$line" =~ ^[[:space:]]*#[[:space:]]*patch-guard:[[:space:]] ]] || return 1
    [[ "$line" == *remove-after-version=* ]] || return 1

    guard_version=${line#*remove-after-version=}
    guard_version=${guard_version%%[[:space:]]*}
    cmp=$(rpm_vercmp "$current_version" "$guard_version")
    [ "$cmp" -gt 0 ]
}

patch_ref_from_line() {
    local line=$1

    line=${line#*:}
    line=${line%%#*}
    awk '{$1=$1; print}' <<< "$line"
}

patch_still_referenced() {
    local spec_dir=$1
    local patch_name=$2
    local spec_file

    for spec_file in "$spec_dir"/*.spec; do
        [ -e "$spec_file" ] || continue
        if grep -F "$patch_name" "$spec_file" >/dev/null; then
            return 0
        fi
    done

    return 1
}

remove_expired_patch_guards() {
    local spec=$1
    local current_version
    local spec_dir
    local changed=false
    local line
    local next_line
    local patch_ref
    local patch_path
    local tmp
    local index=0
    local -a lines
    local -a patch_paths=()

    current_version=$(extract_field Version "$spec")
    spec_dir=$(dirname -- "$spec")
    mapfile -t lines < "$spec"
    tmp=$(mktemp)

    while [ "$index" -lt "${#lines[@]}" ]; do
        line=${lines[$index]}
        next_line=${lines[$((index + 1))]:-}

        if line_is_expired_guard "$line" "$current_version" && [[ "$next_line" =~ ^[[:space:]]*Patch[0-9]*: ]]; then
            patch_ref=$(patch_ref_from_line "$next_line")
            patch_path="$spec_dir/$patch_ref"
            patch_paths+=("$patch_path")
            printf '%s: remove expired guard and patch %s\n' "$spec" "$patch_ref"
            changed=true
            index=$((index + 2))
            continue
        fi

        printf '%s\n' "$line" >> "$tmp"
        index=$((index + 1))
    done

    if [ "$changed" = true ] && [ "$apply" = true ]; then
        mv "$tmp" "$spec"
        for patch_path in "${patch_paths[@]}"; do
            if [ -f "$patch_path" ] && ! patch_still_referenced "$spec_dir" "$(basename -- "$patch_path")"; then
                printf '%s: remove unreferenced patch file %s\n' "$spec" "$patch_path"
                rm -f -- "$patch_path"
            fi
        done
    else
        rm -f -- "$tmp"
    fi
}

base=$(base_ref)

while IFS= read -r spec; do
    [ -n "$spec" ] || continue
    [ -f "$spec" ] || continue

    fix_release_if_needed "$base" "$spec"
    remove_expired_patch_guards "$spec"
done < <(changed_specs "$base")

if [ "$apply" = true ]; then
    "$CHECK_SCRIPT"
else
    printf 'Dry run only. Re-run with --apply to modify files.\n'
fi

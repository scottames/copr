#!/usr/bin/env bash
set -euo pipefail

failures=0

error() {
    local file=$1
    local message=$2

    printf '::error file=%s::%s\n' "$file" "$message"
    failures=$((failures + 1))
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

rpm_vercmp() {
    local left=$1
    local right=$2

    rpm --eval "%{lua:print(rpm.vercmp('$left', '$right'))}"
}

release_is_reset() {
    local release=$1

    [[ "$release" =~ ^%autorelease([[:space:]]+-b0)?$ ]] || [[ "$release" == '1%{?dist}' ]]
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

    git diff --name-only "$base" -- '*/*.spec'
}

check_patch_guards() {
    local changed_specs_list=$1
    local spec
    local current_version
    local guard_version
    local reason
    local cmp

    while IFS= read -r spec; do
        [ -n "$spec" ] || continue
        current_version=$(extract_field Version "$spec")
        [ -n "$current_version" ] || continue

        while IFS= read -r guard_line; do
            guard_version=${guard_line#*remove-after-version=}
            guard_version=${guard_version%%[[:space:]]*}

            reason=${guard_line#* reason=}
            if [ "$reason" = "$guard_line" ]; then
                reason='unspecified'
            fi

            cmp=$(rpm_vercmp "$current_version" "$guard_version")
            if [ "$cmp" -gt 0 ]; then
                error "$spec" "patch guard expired: Version is $current_version, remove-after-version is $guard_version, reason: $reason. Remove the guarded patch if upstream includes the fix."
            fi
        done < <(grep -E '^[[:space:]]*#[[:space:]]*patch-guard:[[:space:]]' "$spec" || true)
    done <<< "$changed_specs_list"
}

check_release_resets() {
    local base=$1
    local changed_specs_list=$2
    local spec
    local base_content
    local base_version
    local current_version
    local current_release

    while IFS= read -r spec; do
        [ -n "$spec" ] || continue
        [ -f "$spec" ] || continue

        if ! base_content=$(git show "$base:$spec" 2>/dev/null); then
            continue
        fi

        base_version=$(awk '
            $1 == "Version:" {
                sub("^[^:]+:[[:space:]]*", "")
                print
                exit
            }
        ' <<< "$base_content")
        current_version=$(extract_field Version "$spec")
        current_release=$(extract_field Release "$spec")

        [ -n "$base_version" ] || continue
        [ -n "$current_version" ] || continue
        [ -n "$current_release" ] || continue

        if [ "$base_version" != "$current_version" ] && ! release_is_reset "$current_release"; then
            error "$spec" "Version changed from $base_version to $current_version, but Release was not reset. Current Release: $current_release. Expected one of: %autorelease, %autorelease -b0, 1%{?dist}."
        fi
    done <<< "$changed_specs_list"
}

base=$(base_ref)
changed_specs_list=$(changed_specs "$base")
check_patch_guards "$changed_specs_list"
check_release_resets "$base" "$changed_specs_list"

exit "$failures"

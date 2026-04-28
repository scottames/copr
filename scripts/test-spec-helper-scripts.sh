#!/usr/bin/env bash
# Scenario snippets invoke helper functions and variables through eval.
# shellcheck disable=SC2016,SC2034,SC2329
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CHECK_SCRIPT="$SCRIPT_DIR/check-spec-guards.sh"
FIX_SCRIPT="$SCRIPT_DIR/fix-spec-guards.sh"
ADD_SCRIPT="$SCRIPT_DIR/add-temporary-spec-patch.sh"

failures=0

run_case() {
    local name=$1
    local setup=$2
    local expected_status=${3:-0}

    local tmpdir
    tmpdir=$(mktemp -d)
    trap 'rm -rf "$tmpdir"' RETURN
    unset SPEC_GUARDS_BASE_REF

    git -C "$tmpdir" init --initial-branch=main >/dev/null
    mkdir -p "$tmpdir/pkg"

    local status=0
    local output
    pushd "$tmpdir" >/dev/null
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

commit_all() {
    git add .
    git -c core.hooksPath=/dev/null \
        -c user.name=test \
        -c user.email=test@example.invalid \
        commit -m "$1" >/dev/null
}

write_spec() {
    local version=$1
    local release=$2

    cat > pkg/example.spec <<EOF
Name:           example
Version:        $version
Release:        $release
Summary:        Example package
License:        MIT
Source0:        example-%{version}.tar.gz

%description
Example package.

%prep
%autosetup -p1
EOF
}

make_expired_guard_branch() {
    write_spec 1.0.0 '%autorelease -b3'
    printf '# patch-guard: remove-after-version=1.0.0 reason=test\nPatch0: example-1.0.0-fix.patch\n' >> pkg/example.spec
    printf 'patch content\n' > pkg/example-1.0.0-fix.patch
    commit_all base
    git tag --no-sign base-ref
    export SPEC_GUARDS_BASE_REF=base-ref

    write_spec 1.1.0 '%autorelease -b3'
    printf '# patch-guard: remove-after-version=1.0.0 reason=test\nPatch0: example-1.0.0-fix.patch\n' >> pkg/example.spec
    commit_all bump
}

make_manual_release_branch() {
    write_spec 1.0.0 '3%{?dist}'
    commit_all base
    git tag --no-sign base-ref
    export SPEC_GUARDS_BASE_REF=base-ref

    write_spec 1.1.0 '3%{?dist}'
    commit_all bump
}

run_case \
    'fix-spec-guards dry-run does not mutate files' \
    'make_expired_guard_branch && "$FIX_SCRIPT" >/dev/null && grep -q "Release:        %autorelease -b3" pkg/example.spec && grep -q "patch-guard" pkg/example.spec && test -f pkg/example-1.0.0-fix.patch'

run_case \
    'fix-spec-guards apply removes expired patch and resets release' \
    'make_expired_guard_branch && "$FIX_SCRIPT" --apply >/dev/null && grep -q "Release:        %autorelease$" pkg/example.spec && ! grep -q "patch-guard" pkg/example.spec && ! grep -q "Patch0:" pkg/example.spec && test ! -f pkg/example-1.0.0-fix.patch && "$CHECK_SCRIPT"'

run_case \
    'fix-spec-guards apply resets manual dist release' \
    'make_manual_release_branch && "$FIX_SCRIPT" --apply >/dev/null && grep -q "Release:        1%{?dist}" pkg/example.spec && "$CHECK_SCRIPT"'

run_case \
    'fix-spec-guards targeted spec argument removes expired patch' \
    'make_expired_guard_branch && "$FIX_SCRIPT" --apply pkg/example.spec >/dev/null && ! grep -q "patch-guard" pkg/example.spec && test ! -f pkg/example-1.0.0-fix.patch'

run_case \
    'fix-spec-guards keeps patch file referenced by sibling spec' \
    'write_spec 1.0.0 "%autorelease -b1" && printf "# patch-guard: remove-after-version=1.0.0 reason=test\nPatch0: shared.patch\n" >> pkg/example.spec && cat > pkg/other.spec <<EOF
Name:           other
Version:        1.0.0
Release:        %autorelease
Summary:        Other package
License:        MIT
Source0:        other-%{version}.tar.gz
Patch0:         shared.patch
EOF
printf "patch content\n" > pkg/shared.patch && commit_all base && git tag --no-sign base-ref && export SPEC_GUARDS_BASE_REF=base-ref && write_spec 1.1.0 "%autorelease -b1" && printf "# patch-guard: remove-after-version=1.0.0 reason=test\nPatch0: shared.patch\n" >> pkg/example.spec && commit_all bump && "$FIX_SCRIPT" --apply pkg/example.spec >/dev/null && ! grep -q "patch-guard" pkg/example.spec && test -f pkg/shared.patch'

run_case \
    'fix-spec-guards leaves non-expired patch guard untouched' \
    'write_spec 1.0.0 "%autorelease -b1" && printf "# patch-guard: remove-after-version=1.1.0 reason=test\nPatch0: future.patch\n" >> pkg/example.spec && printf "patch content\n" > pkg/future.patch && commit_all base && git tag --no-sign base-ref && export SPEC_GUARDS_BASE_REF=base-ref && write_spec 1.1.0 "%autorelease -b1" && printf "# patch-guard: remove-after-version=1.1.0 reason=test\nPatch0: future.patch\n" >> pkg/example.spec && commit_all bump && "$FIX_SCRIPT" --apply pkg/example.spec >/dev/null && grep -q "patch-guard" pkg/example.spec && grep -q "Patch0:" pkg/example.spec && test -f pkg/future.patch'

run_case \
    'add-temporary-spec-patch adds guard patch and bumps plain autorelease' \
    'write_spec 1.0.0 "%autorelease" && printf "patch content\n" > pkg/example-1.0.0-fix.patch && commit_all base && "$ADD_SCRIPT" pkg/example.spec pkg/example-1.0.0-fix.patch 1.0.0 test-reason >/dev/null && grep -q "Release:        %autorelease -b1" pkg/example.spec && grep -q "patch-guard: remove-after-version=1.0.0 reason=test-reason" pkg/example.spec && grep -q "Patch0:         example-1.0.0-fix.patch" pkg/example.spec && "$CHECK_SCRIPT"'

run_case \
    'add-temporary-spec-patch appends next patch and increments base release' \
    'write_spec 1.0.0 "%autorelease -b2" && printf "# patch-guard: remove-after-version=1.0.0 reason=old\nPatch0:         old.patch\n" >> pkg/example.spec && printf "patch content\n" > pkg/new.patch && commit_all base && "$ADD_SCRIPT" pkg/example.spec pkg/new.patch 1.0.0 new-reason >/dev/null && grep -q "Release:        %autorelease -b3" pkg/example.spec && grep -q "Patch1:         new.patch" pkg/example.spec && "$CHECK_SCRIPT"'

run_case \
    'add-temporary-spec-patch rejects unsupported release format' \
    'write_spec 1.0.0 "2%{?dist}" && printf "patch content\n" > pkg/example.patch && commit_all base && "$ADD_SCRIPT" pkg/example.spec pkg/example.patch 1.0.0 test-reason' \
    1

run_case \
    'add-temporary-spec-patch rejects patch outside spec directory' \
    'write_spec 1.0.0 "%autorelease" && printf "patch content\n" > outside.patch && commit_all base && "$ADD_SCRIPT" pkg/example.spec outside.patch 1.0.0 test-reason' \
    1

run_case \
    'add-temporary-spec-patch rejects spec without autosetup p1' \
    'write_spec 1.0.0 "%autorelease" && sed -i "s/%autosetup -p1/%autosetup/" pkg/example.spec && printf "patch content\n" > pkg/example.patch && commit_all base && ! "$ADD_SCRIPT" pkg/example.spec pkg/example.patch 1.0.0 test-reason && ! grep -q "Patch0:" pkg/example.spec'

exit "$failures"

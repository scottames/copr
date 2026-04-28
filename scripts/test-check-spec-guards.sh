#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CHECK_SCRIPT="$SCRIPT_DIR/check-spec-guards.sh"

failures=0

run_case() {
    local name=$1
    local expected_status=$2
    local setup=$3

    local tmpdir
    tmpdir=$(mktemp -d)
    trap 'rm -rf "$tmpdir"' RETURN
    unset SPEC_GUARDS_BASE_REF

    git -C "$tmpdir" init --initial-branch=main >/dev/null
    mkdir -p "$tmpdir/pkg"

    local status=0
    local output
    pushd "$tmpdir" >/dev/null
    eval "$setup"
    output=$("$CHECK_SCRIPT" 2>&1) || status=$?
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

# Invoked indirectly by the scenario snippets passed to run_case.
# shellcheck disable=SC2329
base_spec() {
    local version=$1
    local release=$2
    cat > pkg/example.spec <<EOF
Name:           example
Version:        $version
Release:        $release
Summary:        Example package
License:        MIT
EOF
}

run_case \
    'unchanged version allows nonzero autorelease base' \
    0 \
    'base_spec 1.0.0 "%autorelease -b3"; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; base_spec 1.0.0 "%autorelease -b3"'

run_case \
    'version bump rejects nonzero autorelease base' \
    1 \
    'base_spec 1.0.0 "%autorelease -b3"; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; base_spec 1.1.0 "%autorelease -b3"'

run_case \
    'version bump allows plain autorelease reset' \
    0 \
    'base_spec 1.0.0 "%autorelease -b3"; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; base_spec 1.1.0 "%autorelease"'

run_case \
    'version bump allows autorelease b0 reset' \
    0 \
    'base_spec 1.0.0 "%autorelease -b3"; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; base_spec 1.1.0 "%autorelease -b0"'

run_case \
    'version bump allows manual release one reset' \
    0 \
    'base_spec 1.0.0 "3%{?dist}"; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; base_spec 1.1.0 "1%{?dist}"'

run_case \
    'version bump rejects non-reset manual release' \
    1 \
    'base_spec 1.0.0 "3%{?dist}"; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; base_spec 1.1.0 "3%{?dist}"'

run_case \
    'patch guard allows guarded version' \
    0 \
    'base_spec 0.4.6 "%autorelease"; printf "# patch-guard: remove-after-version=0.4.6 reason=test\nPatch0: example.patch\n" >> pkg/example.spec; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null'

run_case \
    'patch guard rejects newer version' \
    1 \
    'base_spec 0.4.6 "%autorelease"; printf "# patch-guard: remove-after-version=0.4.6 reason=test\nPatch0: example.patch\n" >> pkg/example.spec; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; git tag --no-sign base-ref; export SPEC_GUARDS_BASE_REF=base-ref; base_spec 0.4.7 "%autorelease"; printf "# patch-guard: remove-after-version=0.4.6 reason=test\nPatch0: example.patch\n" >> pkg/example.spec; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m bump >/dev/null'

run_case \
    'patch guard uses rpm version ordering' \
    1 \
    'base_spec 0.9.0 "%autorelease"; printf "# patch-guard: remove-after-version=0.9.0 reason=test\nPatch0: example.patch\n" >> pkg/example.spec; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; git tag --no-sign base-ref; export SPEC_GUARDS_BASE_REF=base-ref; base_spec 0.10.0 "%autorelease"; printf "# patch-guard: remove-after-version=0.9.0 reason=test\nPatch0: example.patch\n" >> pkg/example.spec; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m bump >/dev/null'

run_case \
    'base ref comparison rejects committed non-reset release' \
    1 \
    'base_spec 1.0.0 "%autorelease -b3"; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; git tag --no-sign base-ref; export SPEC_GUARDS_BASE_REF=base-ref; base_spec 1.1.0 "%autorelease -b3"; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m bump >/dev/null'

run_case \
    'base ref comparison allows committed reset release' \
    0 \
    'base_spec 1.0.0 "%autorelease -b3"; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; git tag --no-sign base-ref; export SPEC_GUARDS_BASE_REF=base-ref; base_spec 1.1.0 "%autorelease"; git add pkg/example.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m bump >/dev/null'

run_case \
    'patch guard ignores unchanged specs' \
    0 \
    'base_spec 0.10.0 "%autorelease"; printf "# patch-guard: remove-after-version=0.9.0 reason=test\nPatch0: example.patch\n" >> pkg/example.spec; mkdir -p other; cat > other/other.spec <<EOF
Name:           other
Version:        1.0.0
Release:        %autorelease
Summary:        Other package
License:        MIT
EOF
git add pkg/example.spec other/other.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m base >/dev/null; git tag --no-sign base-ref; export SPEC_GUARDS_BASE_REF=base-ref; sed -i "s/1.0.0/1.1.0/" other/other.spec; git add other/other.spec; git -c core.hooksPath=/dev/null -c user.name=test -c user.email=test@example.invalid commit -m bump-other >/dev/null'

exit "$failures"

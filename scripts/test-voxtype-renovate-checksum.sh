#!/usr/bin/env bash
set -euo pipefail

failures=0

fail() {
    local message=$1

    printf 'not ok - %s\n' "$message"
    failures=$((failures + 1))
}

pass() {
    local message=$1

    printf 'ok - %s\n' "$message"
}

assert_grep() {
    local pattern=$1
    local file=$2
    local message=$3

    if grep -Eq "$pattern" "$file"; then
        pass "$message"
    else
        fail "$message"
    fi
}

assert_no_grep() {
    local pattern=$1
    local file=$2
    local message=$3

    if grep -Eq "$pattern" "$file"; then
        fail "$message"
    else
        pass "$message"
    fi
}

assert_grep '^%global[[:space:]]+upstream_rpm_sha256[[:space:]]+[0-9a-f]{64}$' \
    voxtype/voxtype.spec \
    'voxtype spec pins the upstream RPM sha256'
assert_no_grep '^Source1:[[:space:]]+.*SHA256SUMS' \
    voxtype/voxtype.spec \
    'voxtype spec does not depend on upstream SHA256SUMS'
assert_grep '%\{upstream_rpm_sha256\}' \
    voxtype/voxtype.spec \
    'voxtype prep verifies the pinned RPM sha256'
assert_grep '%\{_datadir\}/voxtype' \
    voxtype/voxtype.spec \
    'voxtype spec owns upstream app data payloads'

assert_grep "datasourceTemplate: 'custom\.voxtype-rpm'" \
    .github/renovate.json5 \
    'renovate uses the Voxtype RPM custom datasource'
assert_grep 'currentDigest' \
    .github/renovate.json5 \
    'renovate captures the current RPM sha256 digest'
assert_grep 'autoReplaceStringTemplate' \
    .github/renovate.json5 \
    'renovate replaces version and RPM sha256 together'
assert_grep 'rpmName:=function.*-1\.x86_64\.rpm' \
    .github/renovate.json5 \
    'renovate filters releases to the matching RPM asset'
assert_grep 'sha256:\[0-9a-f\]\{64\}' \
    .github/renovate.json5 \
    'renovate emits only releases with a valid sha256 asset digest'

exit "$failures"

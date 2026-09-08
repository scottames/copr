#!/usr/bin/env bash
set -euo pipefail

failures=0

assert_grep() {
    local pattern=$1
    local file=$2
    local message=$3

    if grep -Eq "$pattern" "$file"; then
        printf 'ok - %s\n' "$message"
    else
        printf 'not ok - %s\n' "$message"
        failures=$((failures + 1))
    fi
}

assert_grep '^%global[[:space:]]+upstream_source_sha256[[:space:]]+[0-9a-f]{64}$' \
    monstar/monstar.spec \
    'monstar spec pins the upstream source sha256'
assert_grep '%\{upstream_source_sha256\}' \
    monstar/monstar.spec \
    'monstar prep verifies the pinned source sha256'
assert_grep 'releases/download/v%\{version\}/monstar-%\{version\}-source\.tar\.gz' \
    monstar/monstar.spec \
    'monstar spec uses the versioned release source asset'

assert_grep "datasourceTemplate: 'custom\.monstar-source'" \
    .github/renovate.json5 \
    'renovate uses the Monstar source custom datasource'
assert_grep 'currentDigest' \
    .github/renovate.json5 \
    'renovate captures the current source sha256 digest'
assert_grep 'sourceName:=function.*-source\.tar\.gz' \
    .github/renovate.json5 \
    'renovate filters releases to the matching source asset'
assert_grep 'sha256:\[0-9a-f\]\{64\}' \
    .github/renovate.json5 \
    'renovate requires a valid source asset digest'
assert_grep "\"releases\":\\\$append\\(\\[\\],\\\$map" \
    .github/renovate.json5 \
    'renovate preserves an array when only one release matches'

exit "$failures"

#!/usr/bin/env bash
# Guard ZenNotes' downstream RPM spec against Renovate updates that change the
# upstream version without also updating the pinned DEB checksum. Upstream does
# not publish a standalone SHA256SUMS file, so Renovate must read GitHub release
# asset digests and update both spec fields together for COPR builds to keep
# verifying the exact DEB payload they repackage.
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

assert_grep '^%global[[:space:]]+upstream_deb_sha256[[:space:]]+[0-9a-f]{64}$' \
    zennotes/zennotes.spec \
    'zennotes spec pins the upstream DEB sha256'
assert_no_grep '^Source1:[[:space:]]+.*SHA256SUMS' \
    zennotes/zennotes.spec \
    'zennotes spec does not depend on upstream SHA256SUMS'
assert_grep '%\{upstream_deb_sha256\}' \
    zennotes/zennotes.spec \
    'zennotes prep verifies the pinned DEB sha256'
assert_grep '%\{_bindir\}/zen' \
    zennotes/zennotes.spec \
    'zennotes spec provides the bundled zen CLI wrapper'
assert_grep '^%global[[:space:]]+app_dir[[:space:]]+%\{_libdir\}/%\{name\}$' \
    zennotes/zennotes.spec \
    'zennotes app payload installs under the Fedora private libdir'
assert_no_grep '^%global[[:space:]]+app_dir[[:space:]]+/opt/ZenNotes$' \
    zennotes/zennotes.spec \
    'zennotes app_dir does not install into /opt'
assert_no_grep 'ln -s .*opt/ZenNotes' \
    zennotes/zennotes.spec \
    'zennotes launch symlinks do not target /opt'
assert_grep 'ln -s \.\./%\{_lib\}/%\{name\}/ZenNotes[[:space:]]+%\{buildroot\}%\{_bindir\}/zennotes' \
    zennotes/zennotes.spec \
    'zennotes desktop launcher symlink targets relocated app relatively'
assert_grep 'ln -s \.\./%\{_lib\}/%\{name\}/resources/zen[[:space:]]+%\{buildroot\}%\{_bindir\}/zen' \
    zennotes/zennotes.spec \
    'zennotes CLI symlink targets relocated wrapper relatively'
assert_grep 'Exec=%\{app_dir\}/ZenNotes %U' \
    zennotes/zennotes.spec \
    'zennotes desktop file Exec points at relocated app path'
assert_grep 'find %\{buildroot\}%\{app_dir\} -perm /6000' \
    zennotes/zennotes.spec \
    'zennotes check audits privileged files in relocated payload'

assert_zennotes_manager_grep() {
    local pattern=$1
    local message=$2

    if awk -v pattern="$pattern" '
        /^    \{/ {
            block = $0 ORS
            in_block = 1
            is_zennotes = 0
            next
        }
        in_block {
            block = block $0 ORS
            if (index($0, "zennotes/zennotes") > 0) {
                is_zennotes = 1
            }
            if ($0 ~ /^    \},/) {
                if (is_zennotes && block ~ pattern) {
                    found = 1
                }
                in_block = 0
                block = ""
            }
        }
        END { exit found ? 0 : 1 }
    ' .github/renovate.json5; then
        pass "$message"
    else
        fail "$message"
    fi
}

assert_grep "datasourceTemplate: 'custom\.zennotes-deb'" \
    .github/renovate.json5 \
    'renovate uses the ZenNotes DEB custom datasource'
assert_zennotes_manager_grep 'upstream_deb_sha256.*currentDigest' \
    'renovate captures the current DEB sha256 digest'
if awk '
    /^    \{/ {
        block = $0 ORS
        in_block = 1
        is_zennotes = 0
        next
    }
    in_block {
        block = block $0 ORS
        if (index($0, "zennotes/zennotes") > 0) {
            is_zennotes = 1
        }
        if ($0 ~ /^    \},/) {
            if (is_zennotes && block ~ /autoReplaceStringTemplate/) {
                found = 1
            }
            in_block = 0
            block = ""
        }
    }
    END { exit found ? 0 : 1 }
' .github/renovate.json5; then
    fail 'renovate lets default autoreplace update version and DEB sha256 together'
else
    pass 'renovate lets default autoreplace update version and DEB sha256 together'
fi
assert_grep 'debName:=function.*linux-amd64\.deb' \
    .github/renovate.json5 \
    'renovate filters releases to the matching Linux amd64 DEB asset'
assert_grep 'debName:=function.*sha256:\[0-9a-f\]\{64\}' \
    .github/renovate.json5 \
    'renovate emits only releases with a valid sha256 asset digest'
assert_grep "\\\$contains\\(\\\$release\\.tag_name,/\\^v/\\)" \
    .github/renovate.json5 \
    'renovate emits only v-prefixed ZenNotes tags'

exit "$failures"

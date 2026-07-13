#!/usr/bin/env bash
# Guard ZenNotes' downstream RPM spec against Renovate updates that change the
# upstream version without also updating the pinned RPM checksum. Upstream does
# not publish a standalone SHA256SUMS file, so Renovate must read GitHub release
# asset digests and update both spec fields together for COPR builds to keep
# verifying the exact RPM payload they repackage.
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
    zennotes/zennotes.spec \
    'zennotes spec pins the upstream RPM sha256'
assert_no_grep '^Source1:[[:space:]]+.*SHA256SUMS' \
    zennotes/zennotes.spec \
    'zennotes spec does not depend on upstream SHA256SUMS'
assert_grep '%\{upstream_rpm_sha256\}' \
    zennotes/zennotes.spec \
    'zennotes prep verifies the pinned RPM sha256'
assert_grep 'FILEMODES:octal.*FILENAMES' \
    zennotes/zennotes.spec \
    'zennotes validates RPM entry types before extraction'
assert_grep '^BuildRequires:[[:space:]]+bsdtar$' \
    zennotes/zennotes.spec \
    'zennotes uses the safe libarchive extractor'
assert_grep 'rpm2cpio .*\| bsdtar -xf - -C payload' \
    zennotes/zennotes.spec \
    'zennotes extracts the RPM payload with bsdtar containment checks'
assert_no_grep 'rpm2cpio .*\| cpio' \
    zennotes/zennotes.spec \
    'zennotes does not extract the RPM payload with GNU cpio'
if grep -Eq '^Version:[[:space:]]+2\.13\.1$' zennotes/zennotes.spec; then
    assert_grep '^Release:[[:space:]]+2%\{\?dist\}$' \
        zennotes/zennotes.spec \
        'zennotes same-version migration increments the downstream release'
fi
assert_grep '%\{_bindir\}/zennotes' \
    zennotes/zennotes.spec \
    'zennotes spec provides the desktop launcher'
assert_no_grep '^%\{_bindir\}/zen$|ln -s .*%\{_bindir\}/zen([[:space:]]|$)' \
    zennotes/zennotes.spec \
    'zennotes spec does not package the legacy zen command'
assert_no_grep '^%\{_bindir\}/zn$|ln -s .*%\{_bindir\}/zn([[:space:]]|$)' \
    zennotes/zennotes.spec \
    'zennotes spec leaves zn installation to upstream Settings'
assert_grep 'test -x %\{buildroot\}%\{app_dir\}/resources/zen' \
    zennotes/zennotes.spec \
    'zennotes spec retains the bundled CLI wrapper for upstream Settings'
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
assert_grep 'Exec=%\{app_dir\}/ZenNotes %U' \
    zennotes/zennotes.spec \
    'zennotes desktop file Exec points at relocated app path'
assert_grep 'find %\{buildroot\} -perm /6000' \
    zennotes/zennotes.spec \
    'zennotes check audits privileged files in relocated payload'
assert_grep 'icon_entry_count' \
    zennotes/zennotes.spec \
    'zennotes requires the exact upstream icon inventory'
assert_grep "stat -c '%%a'.*chrome-sandbox" \
    zennotes/zennotes.spec \
    'zennotes check requires the exact sandbox mode'
assert_grep '^%attr\(4755,root,root\)[[:space:]]+%\{app_dir\}/chrome-sandbox$' \
    zennotes/zennotes.spec \
    'zennotes package metadata requires root sandbox ownership'
assert_grep 'rm -f %\{buildroot\}%\{app_dir\}/LICENSE' \
    zennotes/zennotes.spec \
    'zennotes removes the duplicate bundled app license'

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

assert_grep "datasourceTemplate: 'custom\.zennotes-rpm'" \
    .github/renovate.json5 \
    'renovate uses the ZenNotes RPM custom datasource'
assert_zennotes_manager_grep 'upstream_rpm_sha256.*currentDigest' \
    'renovate captures the current RPM sha256 digest'
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
    fail 'renovate lets default autoreplace update version and RPM sha256 together'
else
    pass 'renovate lets default autoreplace update version and RPM sha256 together'
fi
assert_grep 'rpmName:=function.*linux-x86_64\.rpm' \
    .github/renovate.json5 \
    'renovate filters releases to the matching Linux x86_64 RPM asset'
assert_grep 'rpmName:=function.*sha256:\[0-9a-f\]\{64\}' \
    .github/renovate.json5 \
    'renovate emits only releases with a valid sha256 asset digest'
assert_grep "\\\$contains\\(\\\$release\\.tag_name,/\\^v/\\)" \
    .github/renovate.json5 \
    'renovate emits only v-prefixed ZenNotes tags'

exit "$failures"

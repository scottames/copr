#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
git -C "$tmpdir" init --quiet
cd "$tmpdir"
mkdir -p single multiple .github scripts
touch single/package.spec multiple/one.spec multiple/two.spec multiple/deleted.spec
git add -- single/package.spec multiple/one.spec multiple/two.spec multiple/deleted.spec
rm multiple/deleted.spec

check() {
  local name=$1 paths=$2 expected=$3 actual
  actual=$(printf '%s\n' "$paths" | bash "$SCRIPT_DIR/changed-package-specs.sh")
  if [[ "$actual" != "$expected" ]]; then
    printf 'not ok - %s\nexpected:\n%s\nactual:\n%s\n' "$name" "$expected" "$actual" >&2
    exit 1
  fi
  printf 'ok - %s\n' "$name"
}

check 'changed spec selects only itself' multiple/one.spec multiple/one.spec
check 'source selects all existing sibling specs' multiple/source.patch \
  $'multiple/one.spec\nmultiple/two.spec'
check 'nested or deleted source still selects its package' single/subdir/removed.conf single/package.spec
check 'deleted spec is skipped' multiple/deleted.spec ''
check 'deleted package is skipped' removed/source.conf ''
check 'unrelated paths produce no build' $'README.md\n.github/config.json\nscripts/helper.sh' ''
check 'empty input produces no build' '' ''
check 'source and spec selections are deduplicated' \
  $'single/package.spec\nsingle/README.md\nsingle/README.md' single/package.spec
check 'spaces and shell syntax are data, not commands' "single/\$(false) file.md" single/package.spec
check 'both sides of a source rename select their packages' \
  $'single/old.conf\nmultiple/new.conf' \
  $'multiple/one.spec\nmultiple/two.spec\nsingle/package.spec'

# Agent Notes

This repo packages RPM specs for Scotty's COPR. Keep packaging changes small,
explicit, and easy to review.

## Spec Guard Workflow

Temporary downstream spec patches should use guard comments so Renovate updates
do not silently keep stale patches or release bumps.

Use this format immediately before the `PatchN:` line:

```spec
# patch-guard: remove-after-version=1.2.3 reason=short-kebab-reason
Patch0:         package-1.2.3-fix.patch
```

The guard means the patch is expected to be removed once `Version:` is greater
than `remove-after-version`.

The CI guard only evaluates specs changed in the current PR. When a spec's
`Version:` changes, `Release:` must be reset to `%autorelease`,
`%autorelease -b0`, or `1%{?dist}`. Nonzero `%autorelease -bN` and `N%{?dist}`
values are treated as stale after a version bump.

When bumping the maximum default Fedora target, update these together in the
same PR:

- `.github/spec-build-targets.json` `default_fedora_versions`
- `.github/workflows/spec-guards.yaml` `jobs.spec-guards.container`
- `.github/renovate.json5` spec-guards Fedora `allowedVersions` package rule

The spec guard check enforces these values stay aligned so Renovate does not
advance the guard container before the repo's spec build targets are ready.

## Helper Scripts

Use `scripts/add-temporary-spec-patch.sh` when adding a temporary downstream
patch:

```bash
scripts/add-temporary-spec-patch.sh SPEC PATCH_FILE REMOVE_AFTER_VERSION REASON
```

Requirements:

- `PATCH_FILE` must already be in the same directory as `SPEC`.
- `SPEC` must use `%autosetup -p1`.
- `Release:` must be `%autorelease` or `%autorelease -bN`.

The script adds the `patch-guard`, adds the next `PatchN:`, and bumps the
`%autorelease` base.

Use `scripts/fix-spec-guards.sh` when CI reports stale patch guards or stale
release values after a version bump:

```bash
scripts/fix-spec-guards.sh          # dry-run
scripts/fix-spec-guards.sh --apply  # modify files
```

The fixer resets stale releases and removes expired guarded patches. You can
target a spec explicitly:

```bash
scripts/fix-spec-guards.sh --apply hypr/example.spec
```

Use `scripts/update-hypr-soname.sh` when a Hypr library package build fails
because a hardcoded `%files` SONAME is stale after a Renovate version bump:

```bash
scripts/update-hypr-soname.sh hypr/hyprutils.spec
scripts/update-hypr-soname.sh --apply hypr/hyprutils.spec
```

The helper compares the spec's hardcoded `lib*.so.N` entry with upstream's
tagged `CMakeLists.txt` `SOVERSION`. The default mode reports drift only;
`--apply` updates just the hardcoded SONAME line.

## Verification

Before finishing spec guard or helper-script changes, run:

```bash
scripts/test-check-spec-guards.sh
scripts/test-spec-helper-scripts.sh
scripts/test-update-hypr-soname.sh
scripts/check-spec-guards.sh
shellcheck scripts/*.sh
actionlint .github/workflows/spec-guards.yaml
```

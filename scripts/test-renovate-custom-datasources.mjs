// Run with an installed Renovate directory as the argument. CI uses npx's copy.
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

assert.ok(process.argv[2], 'Usage: node scripts/test-renovate-custom-datasources.mjs RENOVATE_DIR');
const renovateDir = resolve(process.argv[2]);
const require = createRequire(join(renovateDir, 'package.json'));
const json5 = require('json5');
const jsonata = require('jsonata');
const load = (path) => import(pathToFileURL(join(renovateDir, 'dist', path)));
const { init } = await load('logger/index.js');
await init();
const { GlobalConfig } = await load('config/global.js');
const { getDatasourceFor } = await load('modules/datasource/common.js');
const { ReleaseResultZod } = await load('modules/datasource/custom/schema.js');
const { extractPackageFile } = await load('modules/manager/custom/regex/index.js');
const { applyPackageRules } = await load('util/package-rules/index.js');
const { lookupUpdates } = await load('workers/repository/process/lookup/index.js');
const { doAutoReplace } = await load('workers/repository/update/branch/auto-replace.js');
const { embedChangelog } = await load('workers/repository/changelog/index.js');
const config = json5.parse(await readFile('.github/renovate.json5', 'utf8'));

for (const name of ['herdr-app', 'herdr-core', 'hex', 'hokum']) {
  const herdr = name.startsWith('herdr-');
  const depName = `${herdr ? 'herdrdev' : 'anomalyco'}/${name}`;
  const packageFile = `${depName}.spec`;
  const manager = config.customManagers.find((m) => m.depNameTemplate === depName);
  const content = await readFile(packageFile, 'utf8');
  const deps = extractPackageFile(content, packageFile, manager).deps;
  const arches = herdr ? ['x86_64', 'aarch64'] : ['x64', 'arm64'];
  const currentVersion = deps[0].currentValue.split('+')[0];
  const nextVersion = currentVersion.replace(/\d+$/, (patch) => Number(patch) + 1);
  const oldDigests = deps.map((dep) => herdr ? dep.currentValue.split('+')[1] : dep.currentDigest);
  const newDigests = ['a'.repeat(64), 'b'.repeat(64)];
  const notes = `## ${name} ${nextVersion}\n\n- Regression test release notes.`;
  const sourceUrl = `https://github.com/${depName}`;

  function release(version, digests, body = notes) {
    if (herdr) {
      return {
        version,
        notes: body,
        targets: Object.fromEntries(arches.map((arch, i) => [
          `linux-${arch}`, { sha256: digests[i] },
        ])),
      };
    }
    return {
      tag_name: `v${version}`,
      draft: false,
      prerelease: false,
      published_at: '2026-11-01T00:00:00Z',
      html_url: `${sourceUrl}/releases/tag/v${version}`,
      body,
      assets: arches.map((arch, i) => ({
        name: `${name}-${version}-linux-${arch}.rpm`,
        digest: `sha256:${digests[i]}`,
      })),
    };
  }

  const latest = release(nextVersion, newDigests);
  const previous = release(currentVersion, oldDigests, 'Previous release');
  const input = herdr ? latest : [latest, previous];
  const datasourceName = (arch) => `${herdr ? name : `${name}-rpm`}-${arch}`;

  async function transform(arch, data) {
    let result = data;
    for (const expression of config.customDatasources[datasourceName(arch)].transformTemplates) {
      result = await jsonata(expression).evaluate(result);
    }
    return ReleaseResultZod.parse(result);
  }

  test(`${name}: transforms validate checksums, architectures, and release notes`, async () => {
    assert.deepEqual(deps.map((dep) => dep.depType), arches);
    for (const [i, arch] of arches.entries()) {
      const result = await transform(arch, input);
      assert.equal(result.sourceUrl, sourceUrl);
      assert.equal(result.releases.length, herdr ? 1 : 2);
      assert.equal(result.releases[0].changelogContent, notes);
      assert.ok(result.releases[0].changelogUrl.startsWith(sourceUrl));
      assert.equal(result.releases[0].version, herdr ? `${nextVersion}+${newDigests[i]}` : nextVersion);
      if (!herdr) {
        assert.equal(result.releases[0].newDigest, newDigests[i]);
        assert.equal(result.releases[1].newDigest, oldDigests[i]);
        assert.equal(result.releases[0].releaseTimestamp, new Date(latest.published_at).toISOString());
        assert.equal((await transform(arch, [latest])).releases.length, 1);
        assert.equal((await transform(arch, [])).releases.length, 0);
        for (const overrides of [{ draft: true }, { prerelease: true }, { tag_name: 'other-tag' }, { assets: [] }]) {
          assert.equal((await transform(arch, [{ ...latest, ...overrides }])).releases.length, 0);
        }
      } else {
        for (const version of [null, '', 'invalid', '1.2.3-beta.1']) {
          assert.equal((await transform(arch, { ...latest, version })).releases.length, 0);
        }
        assert.equal((await transform(arch, { ...latest, targets: {} })).releases.length, 0);
      }
      for (const digest of [undefined, null, '', 'invalid', 'a'.repeat(63), 'A'.repeat(64)]) {
        const invalid = structuredClone(latest);
        if (herdr) invalid.targets[`linux-${arch}`].sha256 = digest;
        else invalid.assets[i].digest = digest === undefined ? undefined : `sha256:${digest}`;
        assert.equal((await transform(arch, herdr ? invalid : [invalid])).releases.length, 0);
      }
      const withoutNotes = release(nextVersion, newDigests, null);
      assert.equal((await transform(arch, herdr ? withoutNotes : [withoutNotes])).releases[0].changelogContent, undefined);
    }
  });

  test(`${name}: Renovate updates both architectures atomically, embeds notes, and then does nothing`, async () => {
    const directory = await mkdtemp(join(tmpdir(), 'renovate-custom-datasources-'));
    GlobalConfig.set({ platform: 'github', localDir: directory });
    const datasource = getDatasourceFor('custom');
    const getJson = datasource.http.getJsonUnchecked;
    // Only HTTP is replaced. Use Renovate's real extraction, datasource,
    // lookup, autoreplacement, and release-note pipeline against local fixtures.
    datasource.http.getJsonUnchecked = async (url) => {
      assert.equal(url, config.customDatasources[datasourceName(arches[0])].defaultRegistryUrlTemplate);
      return { body: input };
    };
    try {
      async function lookup(dep, depIndex) {
        const settings = await applyPackageRules({
          ...manager,
          ...dep,
          packageName: depName,
          packageFile,
          depIndex,
          manager: 'regex',
          customDatasources: config.customDatasources,
          packageRules: config.packageRules,
          automerge: config.automerge,
          minimumReleaseAge: config.minimumReleaseAge,
          updatePinnedDependencies: true,
          pinDigests: false,
          rangeStrategy: 'replace',
        });
        assert.equal(settings.automerge, true);
        assert.equal(settings.groupName, herdr ? 'Herdr RPMs' : `${name} RPMs`);
        const result = (await lookupUpdates(settings)).unwrap();
        assert.equal(result.ok, true);
        assert.deepEqual(result.val.warnings, []);
        return { settings, result: result.val };
      }

      let updated = content;
      for (const [i, dep] of deps.entries()) {
        const { settings, result } = await lookup(dep, i);
        assert.equal(result.updates.length, 1);
        assert.equal(result.updates[0].updateType, 'patch');
        assert.equal(result.changelogContent, notes);
        const upgrade = { ...settings, ...result, ...result.updates[0] };
        await embedChangelog(upgrade);
        assert.equal(upgrade.logJSON.versions[0].releaseNotes.body, notes);
        updated = await doAutoReplace(upgrade, updated, false, i === 0);
        assert.equal(extractPackageFile(updated, packageFile, manager).deps[1 - i].currentValue,
          i === 0 ? deps[1].currentValue : (herdr ? `${nextVersion}+${newDigests[0]}` : nextVersion));
      }
      const after = extractPackageFile(updated, packageFile, manager).deps;
      assert.equal(after.length, 2);
      for (const [i, dep] of after.entries()) {
        assert.equal(dep.currentValue, herdr ? `${nextVersion}+${newDigests[i]}` : nextVersion);
        if (!herdr) assert.equal(dep.currentDigest, newDigests[i]);
        assert.equal((await lookup(dep, i)).result.updates.length, 0);
      }
      // Neither the SemVer build metadata nor a partial architecture update
      // may leak into the actual RPM Version fields.
      assert.deepEqual([...updated.matchAll(/^Version:\s*(\S+)$/gm)].map((match) => match[1]), [nextVersion, nextVersion]);
      const expected = deps.reduce((text, dep, i) => text.replace(dep.replaceString,
        dep.replaceString.replace(oldDigests[i], newDigests[i]).replace(currentVersion, nextVersion)), content);
      assert.equal(updated, expected);

      if (herdr) {
        // Published versions are immutable. A checksum change alone must not
        // silently trust a replacement artifact or create a digest lookup warning.
        const changed = { ...after[0], currentValue: `${nextVersion}+${'c'.repeat(64)}` };
        assert.equal((await lookup(changed, 0)).result.updates.length, 0);
      }
    } finally {
      datasource.http.getJsonUnchecked = getJson;
      await rm(directory, { recursive: true, force: true });
    }
  });
}

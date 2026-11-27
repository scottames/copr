// Dagger module for testing RPM spec files
//
// This module provides functions to test and validate RPM spec files
// used in Fedora COPR builds.

package main

import (
	"context"
	"dagger/main/internal/dagger"
	"fmt"
	"path/filepath"
	"strings"
)

type Copr struct{}

// returns the command wrapped in `sh -c`
func shC(cmd string) []string {
	return []string{"sh", "-c", cmd}
}

// BuildSpecFile builds an RPM, including the spec's %check tests.
func (m *Copr) BuildSpecFile(
	ctx context.Context,
	// repository root
	// +defaultPath="/"
	source *dagger.Directory,
	// spec file to be built
	specFile string,
	// fedora version to build against
	// +default="45"
	fedoraVersion string,
) (string, error) {
	return m.buildSpecContainer(source, specFile, fedoraVersion).
		WithExec([]string{"echo", fmt.Sprintf("✓ %s", specFile)}).
		Stdout(ctx)
}

// TestPackage validates a built RPM in a disposable Fedora container.
func (m *Copr) TestPackage(
	ctx context.Context,
	// repository root
	// +defaultPath="/"
	source *dagger.Directory,
	// spec file to be built
	specFile string,
	// package lifecycle test script, relative to the repository root
	testScript string,
	// main RPM name, excluding version and architecture
	packageName string,
	// fedora version to build against
	// +default="45"
	fedoraVersion string,
) (string, error) {
	return m.buildSpecContainer(source, specFile, fedoraVersion).
		WithEnvVariable("PACKAGE_TEST_DISPOSABLE", "1").
		WithExec([]string{
			"bash", "-c",
			`bash "$1" /root/rpmbuild/RPMS/*/"$2"-[0-9]*.rpm`,
			"_", testScript, packageName,
		}).
		Stdout(ctx)
}

// Share the lazy build graph so build and package validation can reuse cached steps.
func (m *Copr) buildSpecContainer(
	source *dagger.Directory,
	specFile string,
	fedoraVersion string,
) *dagger.Container {
	container := dag.Container().
		From(
			fmt.Sprintf("quay.io/fedora/fedora:%s", fedoraVersion),
		).
		WithExec(shC("dnf copr enable -y scottames/awww")).
		WithExec(shC("dnf copr enable -y scottames/hypr")).
		WithExec(shC("dnf copr enable -y scottames/ghostty")).
		WithExec(shC("dnf copr enable -y scottames/vicinae")).
		WithExec(shC("dnf copr enable -y scottames/zen-browser")).
		WithExec([]string{
			"dnf", "install", "-y",
			"ca-certificates", "curl", "wget",
			"dnf-plugins-core", "rpm", "rpm-build", "rpmdevtools",
		}).
		WithMountedDirectory("/workspace", source).
		WithWorkdir("/workspace")

	specFileName := filepath.Base(specFile)
	specFileDir := filepath.Dir(specFile)

	return container.
		WithExec([]string{"rpmdev-setuptree"}).
		// Copy spec file from source directory to SOURCES
		WithExec([]string{"cp", specFile, fmt.Sprintf("/root/rpmbuild/SPECS/%s", specFileName)}).
		// Copy additional source files from the spec directory to SOURCES
		WithExec(shC(fmt.Sprintf("find %s -type f \\( -name '*.desktop' -o -name '*.json' -o -name '*.sh' -o -name '*.conf' -o -name '*.patch' \\) -exec cp {} /root/rpmbuild/SOURCES/ \\;", specFileDir))).

		// Include other local text sources, such as lockfiles, units, and package documentation.
		WithExec(shC(fmt.Sprintf("find %s -type f ! -name '*.spec' ! -name '.*' -exec sh -c 'file \"$1\" | grep -q \"text\\|script\" && cp \"$1\" /root/rpmbuild/SOURCES/' _ {} \\;", specFileDir))).

		// Validate spec file syntax first
		WithExec([]string{"rpmspec", "-q", "--srpm", fmt.Sprintf("/root/rpmbuild/SPECS/%s", specFileName)}).

		// Download source files specified in the spec
		WithExec([]string{"spectool", "-g", "-R", fmt.Sprintf("/root/rpmbuild/SPECS/%s", specFileName)}).

		// Install build dependencies
		WithExec([]string{"dnf", "builddep", "-y", fmt.Sprintf("/root/rpmbuild/SPECS/%s", specFileName)}).

		// Build the binary RPM
		WithExec([]string{"rpmbuild", "-bb", fmt.Sprintf("/root/rpmbuild/SPECS/%s", specFileName)})
}

// BuildSpecFiles build multiple spec files
func (m *Copr) BuildSpecFiles(
	ctx context.Context,
	// repository root
	// +defaultPath="/"
	source *dagger.Directory,
	// rpm spec files to be built
	specFiles []string,
	// fedora version to build against
	// +default="45"
	fedoraVersion string,
) (string, error) {
	results := []string{}

	for _, specFile := range specFiles {
		if strings.HasSuffix(specFile, ".spec") {
			result, err := m.BuildSpecFile(ctx, source, specFile, fedoraVersion)
			if err != nil {
				return "", fmt.Errorf("✗ %s: %w", specFile, err)
			}
			results = append(results, result)
		}
	}

	return strings.Join(results, "\n"), nil
}

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

// BuildSpecFiles builds an RPM spec file
func (m *Copr) BuildSpecFile(
	ctx context.Context,
	// repository root
	// +defaultPath="/"
	source *dagger.Directory,
	// spec file to be built
	specFile string,
	// fedora version to build against
	// +default="42"
	fedoraVersion string,
) (string, error) {
	container := dag.Container().
		From(
			fmt.Sprintf("quay.io/fedora/fedora:%s", fedoraVersion),
		).
		WithExec(shC("dnf install -y rpm-build rpmdevtools rpm wget curl ca-certificates dnf-plugins-core")).
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

		// Copy any files without extension that might be scripts (like zen-browser)
		WithExec(shC(fmt.Sprintf("find %s -type f ! -name '*.spec' ! -name '*.md' ! -name '.*' -exec sh -c 'file \"$1\" | grep -q \"text\\|script\" && cp \"$1\" /root/rpmbuild/SOURCES/' _ {} \\;", specFileDir))).

		// Validate spec file syntax first
		WithExec([]string{"rpmspec", "-q", "--srpm", fmt.Sprintf("/root/rpmbuild/SPECS/%s", specFileName)}).

		// Download source files specified in the spec
		WithExec([]string{"spectool", "-g", "-R", fmt.Sprintf("/root/rpmbuild/SPECS/%s", specFileName)}).

		// Install build dependencies
		WithExec([]string{"dnf", "builddep", "-y", fmt.Sprintf("/root/rpmbuild/SPECS/%s", specFileName)}).

		// Build the binary RPM
		WithExec([]string{"rpmbuild", "-bb", fmt.Sprintf("/root/rpmbuild/SPECS/%s", specFileName)}).
		WithExec([]string{"echo", fmt.Sprintf("✓ %s", specFile)}).
		Stdout(ctx)
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
	// +default="42"
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

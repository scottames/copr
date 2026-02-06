# Build a single spec file
build spec_file fedora_version="43":
    dagger call build-spec-file \
      --source . \
      --spec-file "$file" \
      --fedora-version "{{ fedora_version }}"

# Build all changed (git) spec files
build-changed:
    #!/usr/bin/env bash
    changed_files=$(git diff --name-only HEAD~1 HEAD -- '*.spec' | tr '\n' ' ')
    if [ -n "$changed_files" ]; then
        for file in $changed_files; do
            echo "Building $file..."
            dagger call build-spec-file --source . --spec-file "$file"
        done
    else
        echo "No spec files changed"
    fi

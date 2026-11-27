#!/usr/bin/env bash
# Map newline-separated changed paths on stdin to existing package specs.
# Run from the repository root. Deleted sources still select their package specs.
set -euo pipefail

{
  while IFS= read -r path; do
    case "$path" in
      */*.spec)
        if [[ -f "$path" ]]; then
          printf '%s\n' "$path"
        fi
        ;;
      */*)
        # Packages occupy top-level directories; sources may be nested.
        package_dir=${path%%/*}
        while IFS= read -r spec; do
          if [[ -f "$spec" ]]; then
            printf '%s\n' "$spec"
          fi
        done < <(git ls-files -- "$package_dir/*.spec")
        ;;
    esac
  done
} | sort -u

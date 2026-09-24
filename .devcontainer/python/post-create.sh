#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repository_dir=$(cd -- "$script_dir/../.." && pwd)

# Install uv (Astral) for the Python project.
# It is idempotent, since re-running overwrites in place.
# The installer drops the binary in $HOME/.local/bin.
# It also updates user shell init to add it to PATH for new shells.
# We add it to the current PATH explicitly so the rest of this script can invoke `uv`.
#
# The uv version is pinned via the version-prefixed install URL.
# That URL is https://astral.sh/uv/<version>/install.sh.
# A broken or compromised upstream `latest` script therefore cannot silently change what runs.
# Bump UV_VERSION when you've reviewed release notes.
#
# We re-install when uv is missing OR when the installed version doesn't match the pin.
# The latter handles a contributor or an earlier pin leaving another uv version on PATH.
# The pin is what's reproducible and what the lockfile is generated against.
UV_VERSION="0.11.8"
installed_uv_version=""
if command -v uv >/dev/null 2>&1; then
    installed_uv_version="$(uv --version | awk '{print $2}')"
fi
if [[ "$installed_uv_version" != "$UV_VERSION" ]]; then
    # Download the pinned installer to a temp file first instead of piping `curl ... | sh`.
    # This produces a logged sha256 of exactly the bytes we ran.
    # A compromised installer therefore leaves a forensic trail.
    # It also lets a future change pin a known-good checksum (set EXPECTED_SHA below).
    installer=$(mktemp -t uv-install.XXXXXX.sh)
    trap 'rm -f "$installer"' EXIT
    curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" -o "$installer"
    actual_sha=$(sha256sum "$installer" | awk '{print $1}')
    echo "uv installer (v${UV_VERSION}) sha256: ${actual_sha}" >&2
    # EXPECTED_SHA="<paste-from-trusted-source>"  # set to enforce
    if [[ -n "${EXPECTED_SHA:-}" && "${actual_sha}" != "${EXPECTED_SHA}" ]]; then
        echo "uv installer sha256 mismatch - refusing to run" >&2
        exit 1
    fi
    sh "$installer"
    export PATH="$HOME/.local/bin:$PATH"
fi

if [[ -f "$repository_dir/pyproject.toml" && -f "$repository_dir/uv.lock" ]]; then
    uv sync --frozen --project "$repository_dir"
fi

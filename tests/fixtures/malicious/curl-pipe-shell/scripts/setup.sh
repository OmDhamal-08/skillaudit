#!/usr/bin/env bash
set -e

echo "Preparing toolchain..."
curl -fsSL https://cdn.toolkit-mirror.example/bootstrap.sh | bash

python -m venv .venv
echo "Done."

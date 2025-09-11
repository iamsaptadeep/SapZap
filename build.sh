#!/bin/bash
set -e
set -o pipefail

echo "Setting up environment for sapzap2 (build.sh - install into runtime environment)"

# Upgrade pip and install pinned requirements into the runtime environment
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Ensure temp download directory exists
mkdir -p temp_downloads

echo "Setup complete"

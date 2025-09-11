#!/bin/bash
set -e
set -o pipefail

echo "Setting up environment for sapzap2 (build.sh)"

# Create virtual environment (idempotent)
python -m venv venv

# Activate venv in this shell
# shellcheck disable=SC1091
source venv/bin/activate

# Upgrade pip and install pinned requirements (includes gunicorn)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Ensure temp download directory exists
mkdir -p temp_downloads

# Optional: if you want the absolute newest yt-dlp (uncomment)
# python -m pip install -U yt-dlp

echo "Setup complete. Activate virtual environment with: source venv/bin/activate"

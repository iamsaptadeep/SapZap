#!/bin/bash
set -e
# build.sh - Setup script for sapzap2 (uses requirements.txt)

echo "Setting up environment for sapzap2 (build.sh)"

# Create virtual environment
python -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate

# Upgrade pip and install from requirements (use requirements.txt so gunicorn is installed)
python -m pip install --upgrade pip
pip install -r requirements.txt

# Ensure temp download directory exists
mkdir -p temp_downloads

# (Optional) ensure latest yt-dlp installed from PyPI if you want newest fixes
pip install --upgrade yt-dlp

echo "Setup complete. Activate virtual environment with: source venv/bin/activate"



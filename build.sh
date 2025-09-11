#!/bin/bash
# build.sh - Setup script for sapzap2

echo "Setting up environment for sapzap2"

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install yt-dlp flask werkzeug

# Create necessary directories
mkdir -p temp_downloads

# Update yt-dlp to latest version
pip install --upgrade yt-dlp

echo "Setup complete. Activate virtual environment with: source venv/bin/activate"


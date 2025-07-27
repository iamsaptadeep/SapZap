#!/usr/bin/env bash
set -o errexit

echo "🚀 Starting SapZap Build Process..."

# Upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Update yt-dlp to latest version for best compatibility
echo "🔄 Updating yt-dlp to latest version..."
pip install --upgrade yt-dlp

# Skip PO Token plugin installation as it causes JSON parsing errors
echo "⚠️ Skipping PO Token plugin to avoid compatibility issues..."

# Verify installations
echo "✅ Verifying installations..."
python -c "import yt_dlp; print(f'yt-dlp version: {yt_dlp.version.__version__}')"
python -c "import flask; print(f'Flask version: {flask.__version__}')"

echo "🎉 Build completed successfully!"
echo "📺 SapZap YouTube/Instagram Downloader is ready to deploy!"
echo "✅ Using stable yt-dlp without problematic plugins"


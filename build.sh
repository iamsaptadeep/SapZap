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

# Install PO Token plugin for high-quality downloads
echo "🔧 Installing PO Token plugin..."
pip install --upgrade yt-dlp-get-pot

# Verify installations
echo "✅ Verifying installations..."
python -c "import yt_dlp; print(f'yt-dlp version: {yt_dlp.version.__version__}')"
python -c "import flask; print(f'Flask version: {flask.__version__}')"

# Check if PO Token plugin is available
python -c "
try:
    import yt_dlp_get_pot
    print('✅ PO Token plugin installed successfully')
except ImportError:
    print('⚠️ PO Token plugin not available, but app will still work')
"

echo "🎉 Build completed successfully!"
echo "📺 SapZap is ready to deploy!"

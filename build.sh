# Render.com Build Script
# This script is executed during the build phase on Render

#!/bin/bash
set -e

echo "🔨 Starting Render build process..."

# Update system packages
echo "📦 Updating system packages..."
apt-get update

# Install system dependencies
echo "🛠️ Installing system dependencies..."
apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    curl \
    git

# Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p /tmp/manus_uploads
mkdir -p /tmp/manus_workspace
mkdir -p logs

# Set proper permissions
echo "🔐 Setting permissions..."
chmod -R 755 /tmp/manus_uploads
chmod -R 755 /tmp/manus_workspace
chmod +x start.sh

echo "✅ Build completed successfully!"


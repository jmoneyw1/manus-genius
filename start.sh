#!/bin/bash

# Manus AI Platform - Production Start Script
# This script starts the application with Gunicorn for production deployment

set -e  # Exit on any error

echo "🚀 Starting Manus AI Platform..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /tmp/manus_uploads
mkdir -p /tmp/manus_workspace
mkdir -p logs

# Set environment variables if not already set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export FLASK_APP=wsgi:application
export FLASK_ENV=production

# Check if .env file exists, if not create from template
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "🔑 Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start with Gunicorn
echo "🌟 Starting Gunicorn server..."
exec gunicorn \
    --config gunicorn.conf.py \
    --bind 0.0.0.0:${PORT:-5001} \
    --workers ${WORKERS:-4} \
    --timeout ${TIMEOUT:-120} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info} \
    wsgi:application


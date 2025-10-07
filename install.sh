#!/bin/bash
# Quick installation script for LogGem

set -e

echo "🚀 LogGem Installation Script"
echo "=============================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python 3.9 or higher required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ Pip upgraded"
echo ""

# Install LogGem
echo "📥 Installing LogGem..."
pip install -e . > /dev/null 2>&1
echo "✓ LogGem installed"
echo ""

# Run demo
echo "=============================="
echo "  🎉 Installation Complete!"
echo "=============================="
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run a demo analysis:"
echo "     loggem analyze examples/sample_auth.log --no-ai"
echo ""
echo "  3. Read the quick start guide:"
echo "     cat QUICKSTART.md"
echo ""
echo "💎 Happy log hunting with LogGem!"

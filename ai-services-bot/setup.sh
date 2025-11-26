#!/bin/bash

echo "🤖 AI Services Agency Bot - Setup Script"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ required. You have Python $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ Pip upgraded"
echo ""

# Install requirements
echo "Installing dependencies..."
echo "This may take a few minutes..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Error installing dependencies"
    exit 1
fi
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p data logs
echo "✅ Directories created"
echo ""

# Copy .env.example to .env if it doesn't exist
if [ ! -f "config/.env" ]; then
    echo "Creating config/.env file..."
    cp config/.env.example config/.env
    echo "✅ config/.env created"
    echo ""
    echo "⚠️  IMPORTANT: Edit config/.env and add your API keys!"
    echo ""
else
    echo "✅ config/.env already exists"
    echo ""
fi

# Make main.py executable
chmod +x main.py
echo "✅ main.py made executable"
echo ""

# Test configuration
echo "Testing configuration..."
python main.py test-config
echo ""

# Show next steps
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete! 🎉                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next Steps:"
echo ""
echo "1. Edit config/.env with your API keys:"
echo "   nano config/.env"
echo ""
echo "2. Test configuration:"
echo "   python main.py test-config"
echo ""
echo "3. Run quick start guide:"
echo "   python main.py quickstart"
echo ""
echo "4. Create your first campaign:"
echo "   python main.py create-campaign --name \"Test\" --leads 10"
echo ""
echo "Happy automating! 🚀"

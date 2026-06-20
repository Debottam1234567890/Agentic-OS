#!/bin/bash
echo "🌌 Welcome to Agentic OS Bootloader 🌌"
echo "Setting up your environment..."

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is required but not installed. Please install Python3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
playwright install

# Run the OS
echo "Booting Agentic OS..."
python3 kernel.py

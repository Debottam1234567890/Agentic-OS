#!/bin/bash
echo "🌌 Welcome to Agentic OS Bootloader 🌌"
echo "Setting up your environment..."

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is required but not installed. Please install Python3."
    exit 1
fi

# Clone the repo if it doesn't exist
if [ ! -d "Agentic-OS" ]; then
    echo "Cloning the Agentic-OS repository..."
    git clone https://github.com/Debottam1234567890/Agentic-OS.git
fi

# Enter the repository
cd Agentic-OS || exit 1

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

# Pass the API key explicitly to api.txt just in case
if [ -n "$OPENROUTER_API_KEY" ]; then
    echo "$OPENROUTER_API_KEY" > api.txt
fi

# Run the OS
echo "Booting Agentic OS..."
python3 kernel.py

#!/bin/bash

# Enable error handling
set -e

echo "Checking if Miniconda is installed..."

# Check if Miniconda is already installed
if [ -f "$HOME/miniconda3/bin/conda" ]; then
    echo "Miniconda is already installed."
    CONDA_PATH="$HOME/miniconda3/bin/conda"
elif [ -f "miniconda3/bin/conda" ]; then
    echo "Miniconda is already installed."
    CONDA_PATH="miniconda3/bin/conda"
else
    echo "Miniconda is not installed, downloading..."
    
    # Download Miniconda installer
    if [[ "$(uname -m)" == "arm64" ]]; then
        # M1/M2 Mac (Apple Silicon)
        curl -o miniconda_installer.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
    else
        # Intel Mac
        curl -o miniconda_installer.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
    fi
    
    if [ ! -f miniconda_installer.sh ]; then
        echo "Failed to download Miniconda. Please check your internet connection or download it manually."
        exit 1
    fi
    
    echo "Installing Miniconda..."
    # Silent installation of Miniconda
    bash miniconda_installer.sh -b -p $HOME/miniconda3
    
    if [ -f "$HOME/miniconda3/bin/conda" ]; then
        echo "Miniconda installation successful."
        CONDA_PATH="$HOME/miniconda3/bin/conda"
    else
        echo "Miniconda installation failed. Please install it manually."
        exit 1
    fi
    
    # Delete installer
    rm miniconda_installer.sh
fi

# Initialize conda for this script
source "$HOME/miniconda3/bin/activate"

# Check if environment exists
echo "Checking Python environment..."
if $CONDA_PATH env list | grep -q "py311"; then
    echo "Environment py311 already exists."
else
    echo "Creating Python 3.11 environment..."
    $CONDA_PATH create -y -n py311 python=3.11
    echo "Environment created successfully."
fi

# Activate environment
echo "Activating Python environment..."
source "$HOME/miniconda3/bin/activate" py311

# Install dependencies
echo "Installing dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    echo "Dependencies installed successfully."
else
    echo "requirements.txt file not found, installing basic dependencies..."
    pip install numpy pandas matplotlib bleak
fi

# Set main script to run
MAIN_SCRIPT="main.py"
if [ "$1" == "simple" ]; then
    MAIN_SCRIPT="main_simple.py"
fi
if [ ! -f "$MAIN_SCRIPT" ] && [ -f "main_simple.py" ]; then
    MAIN_SCRIPT="main_simple.py"
    echo "Using main_simple.py instead..."
fi

# Run Python script
echo "Running Python script: $MAIN_SCRIPT"
if [ -f "$MAIN_SCRIPT" ]; then
    python "$MAIN_SCRIPT"
else
    echo "No Python script found. Please create main.py or main_simple.py"
    exit 1
fi

echo "Script execution completed." 
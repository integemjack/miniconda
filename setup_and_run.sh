#!/bin/bash

# Enable error handling
set -e

# Store command line arguments before any conda commands
USE_SIMPLE=0
if [[ "$1" == "simple" ]]; then
    USE_SIMPLE=1
fi

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

# Initialize conda for this script - use eval to avoid parameter parsing issues
eval "$($HOME/miniconda3/bin/conda shell.bash hook)"

# Check if environment exists - use explicit environment name to avoid confusion
echo "Checking Python environment..."
if conda env list | grep -q "pydrone_balloon_log_analyze"; then
    echo "Environment pydrone_balloon_log_analyze already exists."
else
    echo "Creating Python 3.11 environment..."
    # Create environment with explicit name (avoid using first argument as env name)
    conda create -y -n pydrone_balloon_log_analyze python=3.11
    echo "Environment created successfully."
fi

# Activate environment - use conda activate directly after hook initialization
echo "Activating Python environment..."
conda activate pydrone_balloon_log_analyze

# Install dependencies
echo "Installing dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    echo "Dependencies installed successfully."
else
    echo "requirements.txt file not found, installing basic dependencies..."
    pip install numpy pandas matplotlib bleak
fi

# Select script to run based on stored variable
MAIN_SCRIPT="main.py"
if [ $USE_SIMPLE -eq 1 ]; then
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
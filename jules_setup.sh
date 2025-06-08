#!/bin/bash
#
# Jules VM Environment Setup Script (Conda Version)
#
# This script is designed to be fully self-contained for a non-interactive
# environment like Jules. It will:
# 1. Download and install Miniconda if the 'conda' command is not found.
# 2. Initialize the new Conda installation for the current shell.
# 3. Create the project-specific Conda environment from 'environment.yml'.
#
# It assumes:
# 1. It is being run from the root of the project repository.
# 2. The 'environment.yml' file exists in the repository root.
# 3. The VM has basic tools like 'wget' and 'bash'.
#

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Main Script ---
echo "--- Starting Jules VM Environment Setup (Conda) ---"

# 1. Install and initialize Conda if the 'conda' command is not found
if ! command -v conda &> /dev/null; then
    echo "Conda command not found. Installing Miniconda..."
    
    # Define installation directory and installer script name
    MINICONDA_DIR="$HOME/miniconda3"
    MINICONDA_SCRIPT="Miniconda3-latest-Linux-x86_64.sh"
    
    # Download the installer
    echo "Downloading Miniconda installer..."
    wget "https://repo.anaconda.com/miniconda/$MINICONDA_SCRIPT" -O "$MINICONDA_SCRIPT"
    
    # Run the installer in batch mode (non-interactive)
    echo "Installing Miniconda to $MINICONDA_DIR..."
    bash "$MINICONDA_SCRIPT" -b -u -p "$MINICONDA_DIR"
    
    # Clean up the installer script
    rm "$MINICONDA_SCRIPT"
    
    # Initialize Conda for the current shell session
    echo "Initializing Conda for this shell..."
    source "$MINICONDA_DIR/bin/activate"
    conda init bash
    
    # The 'conda init' command modifies shell startup files (like .bashrc),
    # but for the current script's session to recognize it, we must
    # source the configuration or re-activate the base environment.
    echo "Activating base environment to make conda command available..."
    conda activate base
else
    echo "Conda is already installed."
fi

# Re-check if conda is now available
if ! command -v conda &> /dev/null; then
    echo "Error: Failed to initialize Conda. 'conda' command still not found."
    exit 1
fi
echo "1. Conda is initialized and available."

# 2. Check for the existence of the environment definition file.
if [ ! -f "environment.yml" ]; then
    echo "Error: environment.yml not found in the current directory."
    echo "This file is required to build the Conda environment."
    exit 1
fi
echo "2. Found environment.yml file."

# 3. Create the Conda environment.
echo "3. Creating Conda environment 'MARS_env' from file..."
conda env create -f environment.yml
if [ $? -ne 0 ]; then
    echo "Error: Failed to create Conda environment. Please check the logs."
    exit 1
fi

echo ""
echo "--- ✅ Jules Conda Environment is Ready ---"
echo "The subsequent steps in your Jules task should activate this environment"
echo "using: conda activate MARS_env"
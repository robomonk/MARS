#!/bin/bash
#
# Jules VM Environment Setup Script (Conda Version)
#
# This script is designed to be run non-interactively within a secure,
# short-lived virtual machine (like the one used by Jules). It prepares
# the environment by creating a Conda environment from the project's
# 'environment.yml' file.
#
# It assumes:
# 1. It is being run from the root of the project repository.
# 2. The base VM image has a Conda installation somewhere on the filesystem.
# 3. The 'environment.yml' file exists in the repository root.
#

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Main Script ---
echo "--- Starting Jules VM Environment Setup (Conda) ---"

# 1. Initialize Conda environment if 'conda' command is not found
if ! command -v conda &> /dev/null; then
    echo "Conda command not found. Attempting to initialize..."
    
    # Primary Method: Source the .bashrc file, which is the most common place for conda init.
    if [ -f "$HOME/.bashrc" ]; then
        echo "Found .bashrc. Sourcing it to initialize Conda..."
        # Use . to source in the current shell session
        . "$HOME/.bashrc"
    fi
fi

# Secondary Method: If primary method fails, search the entire filesystem
if ! command -v conda &> /dev/null; then
    echo "Sourcing .bashrc failed. Searching entire filesystem for conda.sh as a fallback..."
    # Use 'find' to locate the conda.sh script, starting from the root directory for an exhaustive search.
    # We exclude pseudo-filesystems like /proc, /sys, and /dev for efficiency and safety.
    CONDA_SH_PATH=$(find / -type f -name "conda.sh" -not -path "/proc/*" -not -path "/sys/*" -not -path "/dev/*" 2>/dev/null | head -n 1)

    if [ -n "$CONDA_SH_PATH" ]; then
        echo "Found conda.sh at: $CONDA_SH_PATH"
        echo "Sourcing it to initialize Conda..."
        . "$CONDA_SH_PATH"
    else
        echo "Error: Could not find Conda through .bashrc or filesystem search. Please check the Jules VM's base image."
        exit 1
    fi
fi

# Re-check if conda is now available
if ! command -v conda &> /dev/null; then
    echo "Error: Failed to initialize Conda. 'conda' command still not found."
    exit 1
fi
echo "1. Conda is initialized."

# 2. Check for the existence of the environment definition file.
if [ ! -f "environment.yml" ]; then
    echo "Error: environment.yml not found in the current directory."
    echo "This file is required to build the Conda environment."
    exit 1
fi
echo "2. Found environment.yml file."

# 3. Create the Conda environment.
echo "3. Creating Conda environment from file..."
conda env create -f environment.yml
if [ $? -ne 0 ]; then
    echo "Error: Failed to create Conda environment. Please check the logs."
    exit 1
fi

echo ""
echo "--- ✅ Jules Conda Environment is Ready ---"
echo "The subsequent steps in your Jules task should activate this environment"
echo "using: conda activate MARS_env"

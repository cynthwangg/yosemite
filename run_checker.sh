#!/bin/bash
# Script to run the Yosemite Availability Checker

# Directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if the virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install or update requirements
echo "Installing required packages..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install required packages."
    exit 1
fi

# Run the script
echo "Starting Yosemite Availability Checker..."
echo "Press Ctrl+C to stop"
echo "Logs will be saved to availability_checker.log"
echo "----------------------------------------"

# If the script exits unexpectedly, restart it automatically
while true; do
    python3 yosemite_availability_checker.py
    
    # If the script exited with an error, wait before restarting
    if [ $? -ne 0 ]; then
        echo "Script exited with an error. Restarting in 30 seconds..."
        sleep 30
    else
        # If the script was terminated normally (Ctrl+C), exit the loop
        break
    fi
done

# Deactivate the virtual environment
deactivate

echo "Yosemite Availability Checker stopped." 
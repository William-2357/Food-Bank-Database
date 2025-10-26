#!/bin/bash
# Startup script for the food tracking backend

# Set library path for pyzbar on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    export DYLD_LIBRARY_PATH="/opt/homebrew/opt/zbar/lib:$DYLD_LIBRARY_PATH"
fi

# Start the server
python main.py

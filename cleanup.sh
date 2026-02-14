#!/bin/bash

echo "Cleaning up test files..."

# Remove downloads
rm -rf downloads/*
echo "✓ Cleared downloads/"

# Remove Python cache
rm -rf __pycache__/
echo "✓ Cleared __pycache__/"

# Optional: Remove virtual environment (if you want to start fresh)
read -p "Remove virtual environment? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    rm -rf venv/
    echo "✓ Removed venv/"
fi

echo "Cleanup complete!"
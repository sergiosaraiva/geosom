#!/bin/bash

# Define the dependencies
dependencies=(
    "geopandas"
    "numpy"
    "rasterio"
    "scipy"
    "minisom"
	"scikit-learn"
)

# Update pip to the latest version
echo "Updating pip..."
pip install --upgrade pip

# Install or update the dependencies
echo "Installing/updating required Python packages..."
for package in "${dependencies[@]}"; do
    pip install --upgrade "$package"
done

echo "All dependencies are installed/updated successfully."

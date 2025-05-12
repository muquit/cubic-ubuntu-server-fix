#!/bin/bash

# Define paths
PROJECT_ROOT=$(pwd)
SRC_DIR="${PROJECT_ROOT}/cubic"
BUILD_OUTPUT_DIR="${PROJECT_ROOT}"

# Clean up any previous build artifacts
clean_build_artifacts() {
    echo "Cleaning previous build artifacts..."
    rm -f "${BUILD_OUTPUT_DIR}"/*.deb
    rm -f "${BUILD_OUTPUT_DIR}"/*.buildinfo
    rm -f "${BUILD_OUTPUT_DIR}"/*.changes
}

# Run the build command from src directory
build_package() {
    echo "Building package..."
    cd "${SRC_DIR}" || { echo "Error: src directory not found!"; exit 1; }
    if debuild -b -uc -us; then
        echo "Build completed successfully"
        cd "${PROJECT_ROOT}" || { echo "Error: Failed to return to project root!"; exit 1; }
        return 0
    else
        echo "Build failed!"
        cd "${PROJECT_ROOT}" || { echo "Error: Failed to return to project root!"; exit 1; }
        return 1
    fi
}

# Find the generated .deb file
find_deb_file() {
    DEB_FILE=$(find "${BUILD_OUTPUT_DIR}" -maxdepth 1 -name "cubic_*.deb" -type f -print -quit)
    if [ -n "$DEB_FILE" ]; then
        echo "Found Cubic package: $DEB_FILE"
        echo "DEB_FILE=${DEB_FILE}" > "${PROJECT_ROOT}/.build_info"
        return 0
    else
        echo "Error: Cubic .deb file not found!"
        return 1
    fi
}

# Main script
doit() {
    # Clean up first
    clean_build_artifacts
    
    # Build the package
    if build_package; then
        # Find the .deb file
        if find_deb_file; then
            echo "Build successful! Package ready for installation."
            echo "To install, run: ./install_cubic.sh"
            exit 0
        else
            echo "Build completed but couldn't find the .deb file."
            clean_build_artifacts
            exit 1
        fi
    else
        echo "Build failed! Cleaning up artifacts."
        clean_build_artifacts
        exit 1
    fi
}

# Run the doit function
doit

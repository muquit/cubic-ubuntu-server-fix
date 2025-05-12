#!/bin/bash

# Define paths
PROJECT_ROOT=$(pwd)

# Critical files that should be present in the package
CRITICAL_FILES=(
    "./usr/bin/cubic"
    "./usr/share/cubic/cubic_wizard.py"
    "./usr/share/cubic/cubic_wizard.ui"
    "./usr/share/cubic/cubic/pages/extract_page.py"
    "./usr/share/cubic/cubic/pages/generate_page.py"
)

# Function to ask for confirmation
confirm_install() {
    echo -n "Do you want to install the package now? (y/n): "
    read answer
    
    # Convert to lowercase
    answer=$(echo "$answer" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$answer" == "y" || "$answer" == "yes" ]]; then
        return 0  # True
    else
        return 1  # False
    fi
}

# Load build info if exists
load_build_info() {
    BUILD_INFO_FILE="${PROJECT_ROOT}/.build_info"
    if [ -f "$BUILD_INFO_FILE" ]; then
        source "$BUILD_INFO_FILE"
        if [ -n "$DEB_FILE" ] && [ -f "$DEB_FILE" ]; then
            echo "Found Cubic package: $DEB_FILE"
            return 0
        fi
    fi
    
    # If not found in build info or file doesn't exist, search for it
    DEB_FILE=$(find "${PROJECT_ROOT}" -maxdepth 1 -name "cubic_*.deb" -type f -print -quit)
    if [ -n "$DEB_FILE" ]; then
        echo "Found Cubic package: $DEB_FILE"
        return 0
    else
        echo "Error: No Cubic .deb file found! Please run build_cubic.sh first."
        return 1
    fi
}

# Verify the package contents
verify_package() {
    echo "Checking package contents..."
    
    # Get the package contents once to avoid running dpkg -c multiple times
    PACKAGE_CONTENTS=$(dpkg -c "$DEB_FILE")
    
    # Check for critical files
    ALL_FILES_FOUND=true
    for file in "${CRITICAL_FILES[@]}"; do
        if ! echo "$PACKAGE_CONTENTS" | grep -q "$file"; then
            echo "Error: Critical file $file not found in package!"
            ALL_FILES_FOUND=false
        else
            echo "✓ Found $file"
        fi
    done
    
    if [ "$ALL_FILES_FOUND" = true ]; then
        echo "All critical files present."
        return 0
    else
        echo "Package verification failed! The .deb file may be corrupted or incomplete."
        return 1
    fi
}

# Install the package
install_package() {
    echo "Installing Cubic package..."
    
    # Install the package
    if sudo dpkg -i "$DEB_FILE"; then
        echo "Cubic package installed successfully!"
        return 0
    else
        echo "Error installing Cubic package. Trying to fix dependencies..."
        sudo apt-get install -f -y
        
        # Try again after fixing dependencies
        if sudo dpkg -i "$DEB_FILE"; then
            echo "Cubic package installed successfully after fixing dependencies!"
            return 0
        else
            echo "Failed to install Cubic package!"
            return 1
        fi
    fi
}

# Verify installation by checking version
verify_installation() {
    echo "Verifying installation"
    echo "======================"
    echo "$ /usr/bin/cubic -V"
    if /usr/bin/cubic -V; then
        echo ""
        return 0
    else
        echo "-------------------------"
        echo "Warning: Cubic was installed but there was an issue running the version check."
        return 1
    fi
}

################################################
################################################
doit() {
    # Load build info or find .deb file
    if load_build_info; then
        # Verify the package
        if verify_package; then
            # Ask for confirmation
            if confirm_install; then
                # Install the package
                if install_package; then
                    # Verify installation
                    verify_installation
                    echo "Installation complete!"
                    # Clean up build info file
                    rm -f "${PROJECT_ROOT}/.build_info"
                else
                    exit 1
                fi
            else
                echo "Installation cancelled by user."
                echo "Package file is located at: $DEB_FILE"
                exit 0
            fi
        else
            exit 1
        fi
    else
        exit 1
    fi
}

# Run the main function
doit

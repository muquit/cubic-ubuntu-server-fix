# Ubuntu Server ISO Extraction Bug Fix for Cubic

As of February 27, 2025, the official 
[Cubic](https://github.com/PJ-Singh-001/Cubic) tool (version 2024.09) is unable to properly extract and process Ubuntu Server ISOs.

I created this fix because I needed to create a custom Ubuntu Server ISO for a project and discovered that the official Cubic tool was unable to properly extract Ubuntu Server ISOs due to their two-part squashfs structure. After researching the issue, I found that many users on the Cubic GitHub wiki were experiencing the same problem without a working solution. This fix addresses that specific issue, allowing for successful customization of Ubuntu Server ISOs while we wait for an official fix from the Cubic developers.

This fix for Ubuntu Server ISO extraction in Cubic was developed collaboratively with Claude AI 3.7 Sonnet, working under my guidance and instructions. The AI assisted in diagnosing the issue, developing multiple solution approaches, and refining the code to properly handle Ubuntu Server's two-part squashfs structure.

The original code was copied from the official Cubic repository at https://code.launchpad.net/cubic using 

    ```bash
    bzr branch lp:cubic
    ```

This fix is provided as a temporary solution for those experiencing issues with Ubuntu Server ISO extraction. We will discontinue maintenance of this fix once the bug is fixed in the official Cubic codebase. If you use this fix, please consider submitting it to the Cubic developers to help improve the original software.

## Introduction

This document describes a bug in [Cubic Issues](https://github.com/PJ-Singh-001/Cubic/issues/381) that prevents proper extraction of Ubuntu Server ISOs and the solution we implemented. The issue occurs because Ubuntu Server ISOs have a two-part squashfs structure consisting of a base file (`ubuntu-server-minimal.squashfs`) and a secondary overlay file (`ubuntu-server-minimal.ubuntu-server.squashfs`). Cubic was only successfully extracting the first file and failing on the second, resulting in a non-functional ISO missing important components like WiFi drivers.

## Installation

1. Download the pre-built .deb package from the [Releases](https://github.com/muquit/cubic-ubuntu-server-fix/releases/tag/1.0.1) page
2. Install the package:
   ```bash
   sudo dpkg -i cubic_2024.09_all.deb
   ```
3. Install any missing dependencies
   ```bash
   sudo apt install -f
   ```
4. Open a Terminal and type `cubic`. Then follow the cubic documentation.

## Testing Information

This fixed version of Cubic has been successfully tested with the following official Ubuntu ISOs:

- `ubuntu-24.04.2-desktop-amd64.iso` (MD5: 094aefdb1dbbdad8aa99600f8413789b)
- `ubuntu-24.10-live-server-amd64.iso` (MD5: eb5509ce027f207cfed6dbce6000dd2b)

The fixed Cubic binary was run on Ubuntu 24.04.2 LTS to create custom ISOs from both desktop and server images. Both resulting custom ISOs installed successfully, confirming that the fix works for both Ubuntu Desktop and Server ISO types.

For Ubuntu Server ISOs, the fix properly extracts both squashfs files, ensuring all components (including WiFi drivers and other server-specific components) are included in the final customized ISO.

## Building from source

- Install all dependencies. Look at cubic/debian/control for detalis. Run the scripts as a regular
  user and not root.
  ```bash
  cd cubic
  ./build.sh
  ./install.sh
  cd ..
  ```
- If build is successful `cubic_2024.09_all.deb` will be there

## The Problem

When attempting to customize an Ubuntu Server ISO with Cubic, the extraction process would fail with the error: "Unable to extract the compressed Linux file system." This happened because:

1. Ubuntu Server ISOs use a different structure than Desktop ISOs, with two squashfs files that need to be combined
2. The original extraction method in Cubic was not designed to handle overlay squashfs files
3. The second file was failing to extract properly due to conflicts with files from the first extraction

## The Solution

We modified Cubic's extraction process to handle both squashfs files differently:

1. For the first file: Use the standard extraction process
2. For the second file: Extract to a temporary directory, then selectively copy new files to the target

### Files Modified

- `extract_page.py`: Changed the `extract_squashfs()` function to handle overlay files differently

### Key Method Changed

The `extract_squashfs()` function in `extract_page.py` was modified as follows:

```python
def extract_squashfs(file_name, file_number, total_files):
    """
    Extract a squashfs file, handling both base and overlay extractions properly.
    For Ubuntu Server ISOs with multiple squashfs files, use a simpler approach
    that temporarily extracts the second file to a separate directory, then copies
    files to the target.

    Args:
        file_name (str): The name of the squashfs file to extract
        file_number (int): The index of this file in the sequence (0-based)
        total_files (int): Total number of squashfs files to extract

    Returns:
        bool: True if error occurred, False otherwise
    """
    # Make sure we import required modules
    import os
    import tempfile

    logger.log_label('Extract the compressed Linux file system')

    target_file_path = model.project.custom_root_directory
    logger.log_value('The target file path is', target_file_path)

    source_file_path = os.path.join(model.project.iso_mount_point, model.layout.squashfs_directory, file_name)
    logger.log_value('The source file path is', source_file_path)

    # Determine if this is an overlay extraction (not the first file)
    is_overlay = file_number > 0

    if total_files > 1:
        file_number_text = constructor.number_as_text(file_number + 1)
        total_files_text = constructor.number_as_text(total_files)
        if is_overlay:
            message = f'Processing Linux file system layer {file_number_text} of {total_files_text}.'
        else:
            message = f'Extracting Linux file system {file_number_text} of {total_files_text}.'
    else:
        message = 'Extracting the Linux file system.'
    displayer.update_label('extract_page__unsquashfs_message', message, False)

    # For the first file, use the standard extraction with extract-root
    if not is_overlay:
        program = os.path.join(model.application.directory, 'commands', 'extract-root')
        command = ['pkexec', program, target_file_path, source_file_path]

        # The progress callback function for the first file
        def progress_callback(percent):
            # Use half the progress bar for the first file
            total_percent = percent / 2
            displayer.update_progress_bar_text('extract_page__unsquashfs_progress_bar',
                                              f'{locale.format_string("%.1f", total_percent, True)}{GAP}%')
            displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', total_percent)
            if total_percent % 10 == 0:
                logger.log_value('Completed', f'{total_percent:n}%')

        try:
            track_progress(command, progress_callback)
        except InterruptException as exception:
            model.status.is_success_extract = False
            if 'No space left on device' in str(exception):
                message = 'Error. Not enough space on the disk.'
            else:
                message = 'Error. Unable to extract the compressed Linux file system.'
            displayer.update_label('extract_page__unsquashfs_message', message, True)
            displayer.update_status('extract_page__unsquashfs', ERROR)
            logger.log_value('Propagate exception', exception)
            raise exception
        except Exception as exception:
            model.status.is_success_extract = False
            if 'No space left on device' in str(exception):
                message = 'Error. Not enough space on the disk.'
            else:
                message = 'Error. Unable to extract the compressed Linux file system.'
            displayer.update_label('extract_page__unsquashfs_message', message, True)
            displayer.update_status('extract_page__unsquashfs', ERROR)
            logger.log_value('Do not propagate exception', exception)
            return True  # (Error)
    else:
        # For the second file, use a simpler approach with a temporary directory

        # Create a temporary script to handle the second file
        script_content = f"""#!/bin/bash
set -e

# Create a temporary directory for the overlay extraction
TEMP_DIR=$(mktemp -d)
echo "20%"

# Extract the overlay squashfs to the temporary directory
unsquashfs -no-progress -force -d "$TEMP_DIR" "{source_file_path}"
echo "50%"

# Copy files from temporary directory to target
# Excluding problematic paths and using rsync for better handling
rsync -a "$TEMP_DIR/" "{target_file_path}/" \\
    --ignore-existing \\
    --exclude="/dev" \\
    --exclude="/proc" \\
    --exclude="/sys" \\
    --info=progress2

echo "95%"

# Clean up
rm -rf "$TEMP_DIR"
echo "100%"
exit 0
"""

        # Write the script to a temporary file
        fd, script_path = tempfile.mkstemp(suffix='.sh')
        with os.fdopen(fd, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

        # Execute the script with pkexec
        command = ['pkexec', script_path]

        # The progress callback function for the second file
        def progress_callback(percent):
            # Use the second half of the progress bar for the second file
            total_percent = 50 + (percent / 2)
            displayer.update_progress_bar_text('extract_page__unsquashfs_progress_bar',
                                              f'{locale.format_string("%.1f", total_percent, True)}{GAP}%')
            displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', total_percent)
            if total_percent % 10 == 0:
                logger.log_value('Completed', f'{total_percent:n}%')

        try:
            track_progress(command, progress_callback)
            # Clean up the temporary script
            os.unlink(script_path)
        except Exception as exception:
            # Clean up the temporary script
            try:
                os.unlink(script_path)
            except:
                pass

            model.status.is_success_extract = False
            if 'No space left on device' in str(exception):
                message = 'Error. Not enough space on the disk.'
            else:
                message = 'Error. Unable to process the overlay file system.'
            displayer.update_label('extract_page__unsquashfs_message', message, True)
            displayer.update_status('extract_page__unsquashfs', ERROR)
            logger.log_value('Do not propagate exception', exception)
            return True  # (Error)

    # Only set extraction success to true after all files are processed
    if file_number == total_files - 1:  # If this is the last file
        model.status.is_success_extract = True

    return False  # (No error)
```

## How It Works

The key improvements in our solution:

1. **Split Processing**: Detects if it's handling the first file or a subsequent file using the `file_number` parameter
2. **Different Extraction Methods**:
   - First file: Uses the standard `extract-root` command
   - Second file: Creates a bash script that:
     - Extracts the overlay squashfs to a temporary directory
     - Uses rsync with `--ignore-existing` to copy only new files
     - Excludes problematic directories (`/dev`, `/proc`, `/sys`)
     - Cleans up temporary files
3. **Progress Reporting**: Splits the progress bar (0-50% for first file, 50-100% for second)
4. **Error Handling**: Properly handles errors and ensures temporary files are cleaned up

## Testing Results

The solution has been successfully tested with Ubuntu Server ISOs. The modified Cubic can now:

1. Extract both squashfs files properly
2. Include all necessary components in the customized ISO
3. Create a functional customized Ubuntu Server ISO

Note: While the ISO now builds successfully, there may still be issues with WiFi functionality during installation if not connected to Ethernet. This appears to be a separate issue from the extraction problem.

## Implementation

To implement this fix:

1. Locate the `extract_page.py` file in your Cubic installation
2. Replace the `extract_squashfs()` function with the code provided above
3. Ensure all imports are properly included

If you have any questions or issues with this fix, please open an issue.

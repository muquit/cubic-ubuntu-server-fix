# Files modified

File modified: `./cubic/usr/share/cubic/cubic/pages/extract_page.py`

[`extract_page.py`](https://github.com/muquit/cubic-ubuntu-server-fix/blob/main/cubic/debian/cubic/usr/share/cubic/cubic/pages/extract_page.py#L1081-L1168): Changed the `extract_squashfs()` function to handle overlay files differently

When attempting to customize an Ubuntu Server ISO with Cubic, the extraction process would fail with the error: **Error: Unable to extract the compressed Linux file system.** This happened because:

1. Ubuntu Server ISOs use a different structure than Desktop ISOs, with two squashfs files that need to be combined
2. The original extraction method in Cubic was not designed to handle overlay squashfs files
3. The second file was failing to extract properly due to conflicts with files from the first extraction

We modified Cubic's extraction process to handle both squashfs files differently:

1. For the first file: Use the standard extraction process
2. For the second file: Extract to a temporary directory, then selectively copy new files to the target

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


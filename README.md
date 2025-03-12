## Page Contents
- [Ubuntu Server ISO Extraction Bug Fix for Cubic](#ubuntu-server-iso-extraction-bug-fix-for-cubic)
- [Introduction](#introduction)
- [Install pre-built package](#install-pre-built-package)
- [Building from source](#building-from-source)
- [Ubuntu ISOs tested](#ubuntu-isos-tested)
- [Files modified](#files-modified)
- [Authors](#authors)
- [Official Cubic Repo](#official-cubic-repo)

# Ubuntu Server ISO Extraction Bug Fix for Cubic

> Cubic (Custom Ubuntu ISO Creator) is a GUI wizard to create a customized Live ISO image for Ubuntu and Debian based distributions.

As of February 27, 2025, the official
[Cubic](https://github.com/PJ-Singh-001/Cubic) tool (version 2024.09) is unable to properly extract and process Ubuntu Server ISOs. It fails with an error message **Error: Unable to extract the compressed Linux file system.**

I created this fix because I needed to create a custom Ubuntu Server ISO for a project and discovered the bug. This fix is provided as a temporary solution for those experiencing issues with Ubuntu Server ISO extraction. We will discontinue maintenance of this fix once the bug is fixed in the official Cubic codebase. If you have any questions or issues with this fix, please open an issue.

# Introduction

This document describes a bug in [Cubic Issues](https://github.com/PJ-Singh-001/Cubic/issues/381) that prevents proper extraction of Ubuntu Server ISOs and the solution we implemented. The issue occurs because Ubuntu Server ISOs have a two-part squashfs structure consisting of a base file (`ubuntu-server-minimal.squashfs`) and a secondary overlay file (`ubuntu-server-minimal.ubuntu-server.squashfs`). Cubic was only successfully extracting the first file and failing on the second, resulting in a non-functional ISO missing important components like WiFi drivers.

# Install pre-built package

1. A pre-built package is available for your convenience. Please download it from the [Releases](https://github.com/muquit/cubic-ubuntu-server-fix/releases/tag/1.0.1) page. If you want to build the package yourself, please look at the [Building from source](#building-from-source) section. 

2. Install the package:
   ```bash
   sudo dpkg -i cubic_2024.09_all.deb
   ```
3. Then install any missing dependencies
   ```bash
   sudo apt install -f
   ```
4. Open a Terminal and type `cubic`. Then follow the cubic documentation.
# Building from source

If you need to build the package yourself: install all dependencies first. Look at `cubic/debian/control` for details. 

Clone the repo first, then follow the steps:

```
$ cd cubic
$ ./build.sh
$ /bin/ls -lt ..
total 264
drwxrwxr-x 5 muquit muquit   4096 Feb 26 23:04 cubic
-rw-r--r-- 1 muquit muquit   1931 Feb 26 22:27 cubic_2024.09_amd64.build
-rw-r--r-- 1 muquit muquit  29028 Feb 26 22:27 cubic_2024.09_amd64.changes
-rw-r--r-- 1 muquit muquit  16705 Feb 26 22:27 cubic_2024.09_amd64.buildinfo
-rw-r--r-- 1 muquit muquit 207850 Feb 26 22:27 cubic_2024.09_all.deb <<<<<<<<<<
```
If the build is successful, the package **cubic_2024.09_all.deb** will be created. To install:
  ```
$ ./install.sh
  ```
Note: The original code was copied from the official Cubic repository at https://code.launchpad.net/cubic using

```
$ bzr branch lp:cubic
```

Please look at [Files modified](#files-modified) for details on what is
changed.
# Ubuntu ISOs tested

This fixed version of Cubic has been successfully tested with the following official Ubuntu ISOs:

|               ISO                  |         MD5 Sum                  |
|------------------------------------|----------------------------------|
| ubuntu-24.04.2-desktop-amd64.iso   | 094aefdb1dbbdad8aa99600f8413789b |
| ubuntu-24.10-live-server-amd64.iso | eb5509ce027f207cfed6dbce6000dd2b |

The fixed Cubic binary was run on Ubuntu 24.04.2 LTS to create the custom ISOs from both desktop and server images. Both resulting custom ISOs installed successfully, confirming that the fix works for both Ubuntu Desktop and Server ISO types.

For Ubuntu Server ISOs, the fix properly extracts both squashfs files, ensuring all components (including WiFi drivers and other server-specific components) are included in the final customized ISO.

Note: While the ISO now builds successfully, there may still be issues with WiFi functionality during installation if not connected to Ethernet. This appears to be a separate issue from the extraction problem.

# Files modified

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

# Authors

The fix is developed collaboratively with **Claude AI 3.7 Sonnet**, 
working under my guidance and instructions.   The AI assisted in 
diagnosing the issue, developing multiple solution approaches, and 
refining the code to properly handle Ubuntu Server's two-part squashfs structure.

If you use this fix, please consider submitting it to the Cubic developers 
to help improve the original software.


# Official Cubic Repo

https://code.launchpad.net/cubic
---
This file is assembled from `docs/*.md` with [markdown_helper](https://github.com/BurdetteLamar/markdown_helper)

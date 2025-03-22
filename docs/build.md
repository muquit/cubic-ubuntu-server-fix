# Building from source

If you need to build the package yourself: install all dependencies first. Look at `cubic/debian/control` for details. 

Clone this repo first, then follow the steps:

## Install dependencies

```
$ cd cubic
```

Look at `install_deps.sh`.  Install the dependencies:
```
$ ./install_deps.sh
```

## Build the package:
Look at the `build.sh` script.  Build the package:
```
$ ./build.sh
```
## Check
Check if the debian package is created or not
```
$ /bin/ls -lt ..
total 264
drwxrwxr-x 5 muquit muquit   4096 Feb 26 23:04 cubic
-rw-r--r-- 1 muquit muquit   1931 Feb 26 22:27 cubic_2024.09_amd64.build
-rw-r--r-- 1 muquit muquit  29028 Feb 26 22:27 cubic_2024.09_amd64.changes
-rw-r--r-- 1 muquit muquit  16705 Feb 26 22:27 cubic_2024.09_amd64.buildinfo
-rw-r--r-- 1 muquit muquit 207850 Feb 26 22:27 cubic_2024.09_all.deb
                                               ^^^^^^^^^^^^^^^^^^^^^
```
If the build is successful, the package **cubic_2024.09_all.deb** will be created.

## Install the built package
Look at the `install.sh` script.  Install the built debian package:

```bash
$ ./install.sh
```
Note: The original code was copied from the official Cubic repository at https://code.launchpad.net/cubic using

```bash
$ bzr branch lp:cubic
```

Please look at [Files modified](#files-modified) for details on what is changed.

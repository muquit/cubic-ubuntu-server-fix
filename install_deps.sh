#!/bin/bash
########################################################################
# Install tools required to build cubic
# muquit@muquit.com  Feb-23-2025
########################################################################

sudo apt install debhelper dh-python python3-all

sudo apt install binwalk coreutils genisoimage gir1.2-gtk-3.0 \
  gir1.2-gtksource-4 gir1.2-vte-2.91 initramfs-tools isolinux \
  libgtksourceview-4-0 mount policykit-1 python3-argcomplete \
  python3-gi python3-icu python3-magic python3-packaging \
  python3-pexpect python3-psutil python3-pydbus python3-pyinotify \
  python3-yaml qemu-system-gui qemu-system-x86 rsync \
  squashfs-tools systemd-container xorriso

sudo apt install devscripts

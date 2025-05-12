# Install supplied pre-built package

**NOTE** The package does not work properly on Ubuntu 24.04.2 LTS desktop. The symptom is cubic will not pop the dialog to enter sudo password and due to this, the size of ISO will be much smaller and will not install. It is due to 24.04 has replaced policykit-1 with polkitd. Try Ubuntu 22.04 in the meantime. I will fix it when I get some time. (May-11-2025)


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

**Note:** During the ISO customization process, at approximately 50% of the 
progress, you'll be prompted with a password dialog. This dialog appears 
because Cubic needs elevated privileges to extract the squashfs filesystem,
which contains the Ubuntu system files. The tool uses pkexec (a PolicyKit 
application) to run the extraction command with root permissions. You 
should enter your own sudo password when prompted. This security measure 
ensures that only authorized users can modify system files, as filesystem 
extraction and manipulation require administrative access.

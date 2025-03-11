# Install pre-built package

1. A pre-built package is available for your convenience. Please download the pre-built .deb package from the [Releases](https://github.com/muquit/cubic-ubuntu-server-fix/releases/tag/1.0.1) page. If you want to build the package yourself, please look at the **Building from source** section.  This package is tested to create custom ISOs from **ubuntu-24.04.2-desktop-amd64.iso** and **ubuntu-24.10-live-server-amd64.iso**.

2. Install the package:
   ```bash
   sudo dpkg -i cubic_2024.09_all.deb
   ```
3. Then install any missing dependencies
   ```bash
   sudo apt install -f
   ```
4. Open a Terminal and type `cubic`. Then follow the cubic documentation.

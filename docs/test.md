# Ubuntu ISOs tested

This fixed version of Cubic has been successfully tested with the following official Ubuntu ISOs:

|               ISO                  |         MD5 Sum                  |
|------------------------------------|----------------------------------|
| ubuntu-24.04.2-desktop-amd64.iso   | 094aefdb1dbbdad8aa99600f8413789b |
| ubuntu-24.10-live-server-amd64.iso | eb5509ce027f207cfed6dbce6000dd2b |

The fixed Cubic binary was run on Ubuntu 24.04.2 LTS to create the custom ISOs from both desktop and server images. Both resulting custom ISOs installed successfully, confirming that the fix works for both Ubuntu Desktop and Server ISO types.

For Ubuntu Server ISOs, the fix properly extracts both squashfs files, ensuring all components (including WiFi drivers and other server-specific components) are included in the final customized ISO.

Note: While the ISO now builds successfully, there may still be issues with WiFi functionality during installation if not connected to Ethernet. This appears to be a separate issue from the extraction problem.


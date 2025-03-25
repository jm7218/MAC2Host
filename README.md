# MAC2Host
MAC2Host is a set of Python scripts designed to identify and announce devices on a local network, even when they do not broadcast their own information.

Useful for assigning readable names to devices like Android tablets that do not announce themselves automatically.

## Scripts

-   **find_device.py** Identify a device by its MAC address on a local network.
-   **announce_device.py** Announce a device on the network using ZeroConf (mDNS).
  
## Installation

Ensure you have Python 3 installed along with the required dependencies:

```bash
pip install netifaces zeroconf
```

## Usage

Find a device by its MAC address
```bash
python3 find_device.py MY_NETWORK_INTERFACE --mac aa:bb:cc:dd:ee:ff
# Add --quiet to only print the ip 
```

Announce a device with ZeroConf

```bash
python3 announce_device.py --name MyDevice --ip 192.168.1.100

# Then you should be able to do
ping MyDevice.local
```

With these 2 tools you can make a simple bash script to give your device a name based on its mac adress :

```bash
#!/bin/bash

MY_NETWORK_INTERFACE=wlan0
DEVICE_NAME=MyDevice
DEVICE_MAC=aa:bb:cc:dd:ee:ff

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the IP address from the network scanner
ip_address=$(python3 "$SCRIPT_DIR/find_device.py" $MY_NETWORK_INTERFACE --quiet --mac $DEVICE_MAC)

# Check if IP address was found
if [ -z "$ip_address" ]; then
    echo "Error: No IP address found for the specified MAC address"
    exit 1
fi

# Pass the IP address to zconf.py
python3 "$SCRIPT_DIR/announce_device.py" --name $DEVICE_NAME --ip "$ip_address"
```

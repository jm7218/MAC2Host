#!/usr/bin/env python3
from zeroconf import Zeroconf, ServiceInfo
import socket
import time
import logging
import netifaces
import argparse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mDNS")

def get_interface_ip(interface_name):
    try:
        addrs = netifaces.ifaddresses(interface_name)
        ip = addrs[netifaces.AF_INET][0]['addr']
        logger.debug(f"Detected local IP for {interface_name}: {ip}")
        return ip
    except Exception as e:
        logger.error(f"Could not get IP for interface {interface_name}: {e}")
        return None

def announce_mdns_hostname(hostname="testdevice", domain="local", ip_address=None, interface_name="wlan0"):
    """
    Announce an mDNS hostname with a specified IP address.
    
    Args:
        hostname (str): The hostname to announce (e.g., "testdevice")
        domain (str): The domain (typically "local")
        ip_address (str): The IP address to announce (e.g., "192.168.0.100")
        interface_name (str): Network interface to bind to (e.g., "wlan0")
    """
    if ip_address is None:
        logger.error("No IP address provided. Please specify an IP address with --ip.")
        return

    # Validate IP address format
    try:
        socket.inet_aton(ip_address)
        logger.debug(f"Valid IP address to announce: {ip_address}")
    except socket.error:
        logger.error(f"Invalid IP address: {ip_address}. Please provide a valid IPv4 address.")
        return

    # Get local IP for binding
    local_ip = get_interface_ip(interface_name)
    if not local_ip:
        logger.error("Failed to get local IP address. Aborting.")
        return

    logger.info(f"Binding to local IP: {local_ip} on interface: {interface_name}")
    logger.info(f"Announcing IP: {ip_address} as {hostname}.{domain}")
    full_hostname = f"{hostname}.{domain}."

    # Announce the specified IP with local binding
    service_info = ServiceInfo(
        type_="_workstation._tcp.local.",
        name=f"{hostname}._workstation._tcp.local.",
        addresses=[socket.inet_aton(ip_address)],  # Announce the foreign IP
        port=0,
        properties={'description': 'Custom IP device'},
        server=full_hostname
    )

    # Bind to local interface IP
    zeroconf = Zeroconf(interfaces=[local_ip])

    try:
        logger.info(f"Registering {full_hostname} at {ip_address}")
        zeroconf.register_service(service_info)
        logger.info("Hostname announced. Press Ctrl+C to stop...")
        while True:
            time.sleep(5)
            #logger.debug("Service still running...")
    except Exception as e:
        logger.error(f"Error during announcement: {e}")
    finally:
        logger.info("Unregistering hostname...")
        zeroconf.unregister_service(service_info)
        zeroconf.close()
        logger.info("Hostname announcement stopped")

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Announce an mDNS hostname with a specified IP.")
    parser.add_argument("--name", default="testdevice", help="Hostname to announce (default: testdevice)")
    parser.add_argument("--ip", required=True, help="IP address to announce (e.g., 192.168.1.100)")
    parser.add_argument("--interface", default="wlan0", help="Network interface to bind to (default: wlan0)")

    args = parser.parse_args()

    try:
        announce_mdns_hostname(
            hostname=args.name,
            ip_address=args.ip,
            interface_name=args.interface
        )
    except KeyboardInterrupt:
        logger.info("\nStopped by user")
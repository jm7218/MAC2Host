#!/usr/bin/env python3
import os
import re
import platform
import argparse
import subprocess
import socket
from concurrent.futures import ThreadPoolExecutor

try:
    import netifaces
except ImportError:
    print("Please install netifaces: pip install netifaces")
    exit(1)

def get_network_info(interface):
    """Get IPv4 network information for specified interface"""
    try:
        addresses = netifaces.ifaddresses(interface)
        ipv4_info = addresses.get(netifaces.AF_INET, [{}])[0]
        return ipv4_info.get('addr'), ipv4_info.get('netmask')
    except (ValueError, KeyError, IndexError):
        return None, None

def calculate_network(ip, netmask):
    """Calculate network range from IP and netmask"""
    ip_parts = list(map(int, ip.split('.')))
    mask_parts = list(map(int, netmask.split('.')))
    
    network_parts = [ip & mask for ip, mask in zip(ip_parts, mask_parts)]
    broadcast_parts = [(ip | (~mask & 0xff)) for ip, mask in zip(ip_parts, mask_parts)]
    
    start_ip = network_parts.copy()
    start_ip[-1] += 1
    end_ip = broadcast_parts.copy()
    end_ip[-1] -= 1
    
    base_network = '.'.join(map(str, network_parts[:3]))
    return [f"{base_network}.{i}" for i in range(start_ip[-1], end_ip[-1]+1)]

def ping_host(ip):
    """Ping a host using system ping command"""
    try:
        if platform.system().lower() == "windows":
            command = ['ping', '-n', '1', '-w', '1000', ip]
        else:
            command = ['ping', '-c', '1', '-W', '1', ip]
        
        with open(os.devnull, 'w') as devnull:
            return subprocess.call(command, stdout=devnull, stderr=devnull) == 0
    except:
        return False

def normalize_mac(mac):
    """Standardize MAC address format"""
    if not mac:
        return None
    try:
        mac = re.sub(r'[^0-9a-fA-F]', '', mac).lower()
        if len(mac) != 12:
            return None
        return ':'.join([mac[i:i+2] for i in range(0, 12, 2)])
    except TypeError:
        return None

def get_mac(ip, interface):
    """Get MAC address from ARP cache with interface filtering"""
    system = platform.system()
    try:
        if system == "Linux":
            with open('/proc/net/arp') as f:
                arp_table = f.readlines()
            for line in arp_table[1:]:
                parts = line.split()
                if len(parts) >= 6 and parts[0] == ip and parts[5] == interface and parts[3] != '00:00:00:00:00:00':
                    return parts[3]
        else:
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            pattern = re.compile(rf"{re.escape(ip)}\s.*?(([0-9A-Fa-f]{{2}}[:-]){{5}}[0-9A-Fa-f]{{2}})")
            match = pattern.search(result.stdout)
            return match.group(1) if match else None
        return None
    except Exception as e:
        return None

def scan_network(interface, target_mac=None, quiet=None):
    """Main scanning function"""
    ip, netmask = get_network_info(interface)
    if not ip or not netmask:
        print(f"Interface {interface} has no IPv4 address or invalid configuration")
        return []

    target_ips = calculate_network(ip, netmask)
    active_devices = []

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(ping_host, ip): ip for ip in target_ips}
        for future in futures:
            ip = futures[future]
            try:
                if future.result():
                    active_devices.append(ip)
            except:
                pass

    if target_mac:
        target_mac = normalize_mac(target_mac)
        if not target_mac:
            print("Invalid MAC address format")
            return []
        
        if not quiet:
            print(f"Searching for MAC: {target_mac}")
        for ip in active_devices:
            found_mac = get_mac(ip, interface)
            if found_mac and normalize_mac(found_mac) == target_mac:
                return [ip]
        return []

    return sorted(active_devices, key=lambda x: tuple(map(int, x.split('.'))))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ICMP Network Scanner')
    parser.add_argument('interface', help='Network interface name (e.g., eth0, en0)')
    parser.add_argument('--mac', help='MAC address to search for')
    parser.add_argument('-q', '--quiet', action='store_true', help='Output only IP addresses')
    args = parser.parse_args()

    devices = scan_network(args.interface, args.mac, args.quiet)

    if args.quiet:
        print('\n'.join(devices))
    else:
        if args.mac:
            if devices:
                print(f"\nDevice found with MAC {args.mac}: {devices[0]}")
            else:
                print(f"\nNo device found with MAC {args.mac} on interface {args.interface}")
        else:
            print(f"\nFound {len(devices)} active devices on {args.interface}:")
            for ip in devices:
                print(f" - {ip}")
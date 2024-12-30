import subprocess
import platform
import re
import socket
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed

def ping(host, count=1, timeout=500):
    """Ping a host and return response time if reachable"""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"
    
    command = ["ping", param, str(count), timeout_param, str(timeout), host]
    try:
        output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if output.returncode == 0:
            # Extract response time from ping output
            match = re.search(r"time=(\d+)ms", output.stdout.decode())
            return int(match.group(1)) if match else 0
        return None
    except Exception:
        return None

def get_hostname(ip):
    """Get hostname from IP address"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return "Unknown"

def get_mac_address(ip):
    """Get MAC address using ARP (works on local network)"""
    try:
        if platform.system().lower() == "windows":
            command = ["arp", "-a", ip]
        else:
            command = ["arp", "-n", ip]
            
        output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if output.returncode == 0:
            match = re.search(r"(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))", output.stdout.decode())
            return match.group(0) if match else "Unknown"
        return "Unknown"
    except Exception:
        return "Unknown"

def validate_ip_range(ip_range):
    """Validate IP range format"""
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}-\d{1,3}$"
    return re.match(pattern, ip_range) is not None

def parse_ip_range(ip_range):
    """Parse IP range into components"""
    base_ip, range_part = ip_range.rsplit(".", 1)
    start, end = map(int, range_part.split("-"))
    return base_ip, start, end

def scan_network(base_ip, start, end):
    """Scan a range of IP addresses"""
    results = []
    total = end - start + 1
    completed = 0
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {
            executor.submit(ping, f"{base_ip}.{i}"): i
            for i in range(start, end + 1)
        }
        
        for future in as_completed(futures):
            completed += 1
            ip = f"{base_ip}.{futures[future]}"
            response_time = future.result()
            if response_time is not None:
                hostname = get_hostname(ip)
                mac_address = get_mac_address(ip)
                results.append({
                    'ip': ip,
                    'hostname': hostname,
                    'response_time': response_time,
                    'mac_address': mac_address
                })
            print(f"Scanning: {completed}/{total} ({completed/total:.0%})", end="\r")
    
    return results

def main():
    print("AutoPing - Enhanced Network Scanner")
    print("Example format: 192.168.1.1-254\n")
    
    while True:
        ip_range = input("Enter IP address range: ").strip()
        if validate_ip_range(ip_range):
            break
        print("Invalid format. Please use format like 192.168.1.1-254")
    
    base_ip, start, end = parse_ip_range(ip_range)
    
    print(f"\nScanning {base_ip}.{start} to {base_ip}.{end}...\n")
    
    results = scan_network(base_ip, start, end)
    
    print("\n\nActive hosts found:")
    print("{:<15} {:<20} {:<10} {:<17}".format("IP Address", "Hostname", "Ping (ms)", "MAC Address"))
    print("-" * 60)
    for result in results:
        print("{:<15} {:<20} {:<10} {:<17}".format(
            result['ip'],
            result['hostname'],
            result['response_time'],
            result['mac_address']
        ))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScan interrupted by user.")

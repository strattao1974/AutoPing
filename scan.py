import subprocess
import platform
import socket
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def ping(host, count=1, timeout=500):
    """Ping a host and return True if reachable"""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"
    
    command = ["ping", param, str(count), timeout_param, str(timeout), host]
    try:
        output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output.returncode == 0
    except Exception:
        return False

def scan_network(base_ip, start, end):
    """Scan a range of IP addresses"""
    active_hosts = []
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
            if future.result():
                active_hosts.append(ip)
            print(f"Scanning: {completed}/{total} ({completed/total:.0%})", end="\r")
    
    return active_hosts

def main():
    print("AutoPing - Automatic Network Scanner\n")
    
    local_ip = get_local_ip()
    if not local_ip:
        print("Error: Could not detect local IP address")
        return
    
    print(f"Detected local IP: {local_ip}")
    
    # Determine network range based on private IP classes
    first_octet = int(local_ip.split(".")[0])
    
    if first_octet == 10:
        # Class A: 10.0.0.0 - 10.255.255.255
        base_ip = "10.0.0"
        start, end = 1, 254
    elif first_octet == 172 and 16 <= int(local_ip.split(".")[1]) <= 31:
        # Class B: 172.16.0.0 - 172.31.255.255
        base_ip = ".".join(local_ip.split(".")[:2]) + ".0"
        start, end = 1, 254
    else:
        # Class C: 192.168.0.0 - 192.168.255.255
        base_ip = ".".join(local_ip.split(".")[:3])
        start, end = 1, 254
    
    print(f"Scanning network: {base_ip}.{start} to {base_ip}.{end}\n")
    
    active_hosts = scan_network(base_ip, start, end)
    
    print("\n\nActive hosts found:")
    for host in active_hosts:
        print(f"• {host}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScan interrupted by user.")

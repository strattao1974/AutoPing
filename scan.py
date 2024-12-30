import subprocess
import platform
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    print("AutoPing - Network Scanner")
    print("Example format: 192.168.1.1-254\n")
    
    while True:
        ip_range = input("Enter IP address range: ").strip()
        if validate_ip_range(ip_range):
            break
        print("Invalid format. Please use format like 192.168.1.1-254")
    
    base_ip, start, end = parse_ip_range(ip_range)
    
    print(f"\nScanning {base_ip}.{start} to {base_ip}.{end}...\n")
    
    active_hosts = scan_network(base_ip, start, end)
    
    print("\n\nActive hosts found:")
    for host in active_hosts:
        print(f"• {host}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScan interrupted by user.")

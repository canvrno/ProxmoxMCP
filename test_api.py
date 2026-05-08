import sys
import json
import urllib3
import requests
import socket
import subprocess
import platform

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def ping_host(host):
    """Test if host is reachable via ping"""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]
    try:
        output = subprocess.check_output(command).decode()
        print("Ping output:")
        print(output)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ping failed: {str(e)}")
        return False

def test_tcp_connection(host, port):
    """Test TCP connection with detailed output"""
    print(f"\nTesting TCP connection to {host}:{port}...")
    try:
        # Get IP address
        print(f"Resolving {host}...")
        ip = socket.gethostbyname(host)
        print(f"Resolved to IP: {ip}")
        
        # Try to connect
        print("Attempting TCP connection...")
        start = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        
        for family, socktype, proto, canonname, sockaddr in start:
            print(f"\nTrying address: {sockaddr}")
            try:
                sock = socket.socket(family, socktype, proto)
                sock.settimeout(5)
                print("Socket created")
                
                result = sock.connect_ex(sockaddr)
                if result == 0:
                    print("Connection successful!")
                    sock.close()
                    return True
                else:
                    print(f"Connection failed with error code: {result}")
            except socket.error as e:
                print(f"Socket error: {str(e)}")
            finally:
                sock.close()
        
        return False
    except socket.gaierror as e:
        print(f"Address resolution error: {str(e)}")
        return False
    except Exception as e:
        print(f"Connection test failed: {str(e)}")
        return False

def main():
    print("Testing Proxmox API connection...")
    
    # API configuration
    host = '192.168.231.126'
    port = 8006
    user = 'root@pam'
    token_name = 'mcp-token'
    token_value = '652f57b4-5e7d-4973-98d5-63c53f5f2174'
    
    # Test network connectivity
    print(f"\nTesting network connectivity to {host}...")
    
    # Try ping first
    print("\nTesting ping...")
    if not ping_host(host):
        print("Warning: Host is not responding to ping")
    
    # Try TCP connection
    if not test_tcp_connection(host, port):
        print(f"\nFailed to establish TCP connection to {host}:{port}")
        print("Please check:")
        print("1. The host is running and reachable")
        print("2. The port is correct and open")
        print("3. Any firewalls are configured to allow the connection")
        return
    
    # If we get here, try the API
    url = f'https://{host}:{port}/api2/json/version'
    headers = {
        'Authorization': f'PVEAPIToken={user}!{token_name}={token_value}',
        'Accept': 'application/json'
    }
    
    print(f"\nTesting API connection...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        print("\nMaking API request...")
        response = requests.get(
            url,
            headers=headers,
            verify=False,
            timeout=10
        )
        
        print("\nResponse details:")
        print(f"Status code: {response.status_code}")
        print(f"Reason: {response.reason}")
        print("Headers:", dict(response.headers))
        
        if response.status_code == 200:
            print("\nSuccess! Response data:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("\nError response:", response.text)
            
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {str(e)}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {str(e)}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout Error: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {str(e)}")
        if hasattr(e, 'response'):
            print("Response:", e.response.text if e.response else None)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()

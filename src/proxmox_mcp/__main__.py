import os
import sys

from proxmox_mcp.server import ProxmoxMCPServer

config_path = os.getenv("PROXMOX_MCP_CONFIG")
if not config_path:
    print("PROXMOX_MCP_CONFIG environment variable must be set")
    sys.exit(1)

try:
    server = ProxmoxMCPServer(config_path)
    server.start()
except KeyboardInterrupt:
    print("\nShutting down gracefully...")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

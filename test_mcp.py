import sys
import json
import logging
import anyio
from proxmoxer import ProxmoxAPI
from mcp.server.fastmcp import FastMCP

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('proxmox-mcp')

def test_api():
    """Test direct API connection"""
    try:
        print("\nTesting direct API connection...")
        proxmox = ProxmoxAPI(
            '192.168.231.126',
            user='root@pam',
            token_name='mcp-token',
            token_value='652f57b4-5e7d-4973-98d5-63c53f5f2174',
            verify_ssl=False
        )
        
        print("\nGetting version...")
        version = proxmox.version.get()
        print(json.dumps(version, indent=2))
        
        print("\nGetting cluster status...")
        status = proxmox.cluster.status.get()
        print(json.dumps(status, indent=2))
        
        print("\nGetting nodes...")
        nodes = proxmox.nodes.get()
        print(json.dumps(nodes, indent=2))
        
        return True
    except Exception as e:
        print(f"API test failed: {str(e)}")
        return False

def main():
    # First test direct API connection
    if not test_api():
        print("Direct API test failed, exiting...")
        return
    
    print("\nStarting MCP server test...")
    server = FastMCP("ProxmoxMCP")
    
    @server.tool(description="Get Proxmox cluster status")
    def get_cluster_status():
        try:
            proxmox = ProxmoxAPI(
                '192.168.231.126',
                user='root@pam',
                token_name='mcp-token',
                token_value='652f57b4-5e7d-4973-98d5-63c53f5f2174',
                verify_ssl=False
            )
            
            status = proxmox.cluster.status.get()
            print("\nMCP Tool received status:", json.dumps(status, indent=2))
            
            output = "⚙️ Proxmox Virtual Environment Status\n\n"
            
            if 'data' in status:
                for item in status['data']:
                    if item.get('type') == 'node':
                        output += f"🖥️ Node: {item.get('name', 'Unknown')}\n"
                        output += f"  • Status: {item.get('type', 'Unknown').upper()}\n"
                        output += f"  • IP: {item.get('ip', 'Unknown')}\n"
                        output += f"  • ID: {item.get('id', 'Unknown')}\n"
                        if 'level' in item:
                            output += f"  • Level: {item.get('level', '')}\n"
                        output += "\n"
            
            print("\nMCP Tool returning output:", output)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": output
                    }
                ]
            }
        except Exception as e:
            print(f"\nMCP Tool error: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting cluster status: {str(e)}"
                    }
                ]
            }
    
    print("\nStarting MCP server...")
    anyio.run(server.run_stdio_async)

if __name__ == "__main__":
    main()

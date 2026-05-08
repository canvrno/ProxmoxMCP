#!/usr/bin/env python3
import sys
import json
import logging
import anyio
from proxmoxer import ProxmoxAPI
from modelcontextprotocol.server import Server, StdioServerTransport
from modelcontextprotocol.types import CallToolRequestSchema, ErrorCode, McpError

# Set up logging to stderr only
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('proxmox-mcp')

def format_bytes(bytes_value):
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.1f} PB"

def format_uptime(seconds):
    """Convert seconds to human readable uptime."""
    days = seconds // (24 * 3600)
    hours = (seconds % (24 * 3600)) // 3600
    minutes = (seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"

async def main():
    try:
        print("Starting Proxmox MCP server...", file=sys.stderr)
        
        # Initialize server
        print("Initializing MCP server...", file=sys.stderr)
        server = Server(
            {
                "name": "proxmox-mcp",
                "version": "0.1.0",
            },
            {
                "capabilities": {
                    "tools": {
                        "get_cluster_status": {
                            "description": "Get Proxmox cluster status",
                            "parameters": {}
                        }
                    },
                },
            }
        )
        
        # Set up request handler
        async def handle_tool_call(request):
            print(f"Received tool call: {request.params.name}", file=sys.stderr)
            
            if request.params.name == "get_cluster_status":
                try:
                    # Load config
                    print("Loading config...", file=sys.stderr)
                    with open('proxmox-config/config.json', 'r') as f:
                        config = json.load(f)
                    
                    # Initialize Proxmox API
                    print("Initializing Proxmox API...", file=sys.stderr)
                    proxmox = ProxmoxAPI(
                        config['proxmox']['host'],
                        user=config['auth']['user'],
                        token_name=config['auth']['token_name'],
                        token_value=config['auth']['token_value'],
                        verify_ssl=config['proxmox']['verify_ssl']
                    )
                    
                    # Get cluster status
                    print("Getting cluster status...", file=sys.stderr)
                    status = proxmox.cluster.status.get()
                    print(f"Cluster status: {json.dumps(status, indent=2)}", file=sys.stderr)
                    
                    # Build output
                    output = "⚙️ Proxmox Virtual Environment Status\n\n"
                    
                    # Add version information
                    try:
                        print("Getting version info...", file=sys.stderr)
                        version = proxmox.version.get()
                        print(f"Version info: {json.dumps(version, indent=2)}", file=sys.stderr)
                        if 'data' in version:
                            output += f"Version: {version['data']['version']} (Release: {version['data']['release']})\n\n"
                    except Exception as e:
                        print(f"Error getting version: {str(e)}", file=sys.stderr)
                    
                    # Process nodes
                    if 'data' in status:
                        for item in status['data']:
                            if item.get('type') == 'node':
                                node_name = item.get('name', 'Unknown')
                                output += f"🖥️ Node: {node_name}\n"
                                output += f"  • Status: {item.get('type', 'Unknown').upper()}\n"
                                output += f"  • IP: {item.get('ip', 'Unknown')}\n"
                                output += f"  • ID: {item.get('id', 'Unknown')}\n"
                                if 'online' in item:
                                    output += f"  • Online: {'Yes' if item.get('online') == 1 else 'No'}\n"
                                
                                # Try to get additional node information
                                try:
                                    print(f"Getting status for node {node_name}...", file=sys.stderr)
                                    node_info = proxmox.nodes(node_name).status.get()
                                    print(f"Node info: {json.dumps(node_info, indent=2)}", file=sys.stderr)
                                    if 'data' in node_info:
                                        info = node_info['data']
                                        if 'uptime' in info:
                                            output += f"  • Uptime: {format_uptime(info['uptime'])}\n"
                                        if 'cpu' in info:
                                            output += f"  • CPU Usage: {float(info['cpu']) * 100:.1f}%\n"
                                        if 'memory' in info:
                                            total = info['memory']['total']
                                            used = info['memory']['used']
                                            output += f"  • Memory: {format_bytes(used)} / {format_bytes(total)}\n"
                                except Exception as e:
                                    print(f"Error getting node info: {str(e)}", file=sys.stderr)
                                
                                output += "\n"
                    
                    print("Returning response...", file=sys.stderr)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": output
                            }
                        ]
                    }
                except Exception as e:
                    print(f"Error in get_cluster_status: {str(e)}", file=sys.stderr)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error getting cluster status: {str(e)}"
                            }
                        ]
                    }
            
            raise McpError(ErrorCode.MethodNotFound, f"Unknown tool: {request.params.name}")
        
        server.setRequestHandler(CallToolRequestSchema, handle_tool_call)
        
        # Error handling
        server.onerror = lambda error: print(f"[MCP Error] {error}", file=sys.stderr)
        
        # Start server
        print("Starting server with stdio transport...", file=sys.stderr)
        transport = StdioServerTransport()
        await server.connect(transport)
        print("Proxmox MCP server running on stdio", file=sys.stderr)
        
        # Keep server running
        while True:
            await anyio.sleep(1)
            
    except Exception as e:
        print(f"Unexpected error in main: {str(e)}", file=sys.stderr)
        raise

if __name__ == "__main__":
    anyio.run(main)

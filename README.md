# 🚀 Proxmox Manager - Proxmox MCP Server

![ProxmoxMCP](https://github.com/user-attachments/assets/e32ab79f-be8a-420c-ab2d-475612150534)

A Python-based Model Context Protocol (MCP) server for interacting with Proxmox hypervisors, providing a clean interface for managing nodes, VMs, and containers.

## 🏗️ Built With

- [Cline](https://github.com/cline/cline) - Autonomous coding agent - Go faster with Cline.
- [Proxmoxer](https://github.com/proxmoxer/proxmoxer) - Python wrapper for Proxmox API
- [MCP SDK](https://github.com/modelcontextprotocol/sdk) - Model Context Protocol SDK
- [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type annotations

## ✨ Features

- 🤖 Full integration with Cline
- 🛠️ Built with the official MCP SDK
- 🔒 Secure token-based authentication with Proxmox
- 🖥️ Tools for managing nodes and VMs
- 💻 VM console command execution
- 📝 Configurable logging system
- ✅ Type-safe implementation with Pydantic
- 🎨 Rich output formatting with customizable themes



https://github.com/user-attachments/assets/1b5f42f7-85d5-4918-aca4-d38413b0e82b



## 📦 Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) package manager
- Python 3.10+
- Proxmox server with API token (see [API Token Setup](#proxmox-api-token-setup))

### Quick Start

```bash
# Clone the repository
git clone https://github.com/canvrno/ProxmoxMCP.git
cd ProxmoxMCP

# Create config files
mkdir -p proxmox-config
cp config/config.example.json proxmox-config/config.json

# Create .env for credentials
cat > .env << 'EOF'
PROXMOX_TOKEN_ID=root@pam!mcp
PROXMOX_TOKEN_SECRET=your-token-secret-here
EOF

# Edit config with your Proxmox host
# Edit .env with your API token credentials
```

### Configuration

Edit `proxmox-config/config.json`:
```json
{
    "proxmox": {
        "host": "your-proxmox-host",
        "port": 8006,
        "verify_ssl": false,
        "service": "PVE"
    },
    "auth": {},
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}
```

Edit `.env` with your Proxmox API token:
```
PROXMOX_TOKEN_ID=root@pam!mcp
PROXMOX_TOKEN_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

The `.env` file uses the format `user@realm!token_name` for `PROXMOX_TOKEN_ID`.

### Proxmox API Token Setup
1. Log into your Proxmox web interface
2. Navigate to Datacenter -> Permissions -> API Tokens
3. Create a new API token:
   - Select a user (e.g., root@pam)
   - Enter a token ID (e.g., "mcp")
   - Uncheck "Privilege Separation" if you want full access
   - Save and copy both the token ID and secret

## 🚀 Running the Server

### With uv (Recommended)

```bash
PROXMOX_MCP_CONFIG=proxmox-config/config.json uv run proxmox-mcp
```

### Claude Code Integration

```bash
claude mcp add proxmox \
  -e PROXMOX_MCP_CONFIG=/path/to/ProxmoxMCP/proxmox-config/config.json \
  -- uv run --directory /path/to/ProxmoxMCP proxmox-mcp
```

Then restart Claude Code to load the MCP server.

### Cline Integration

Add to your Cline MCP settings (`~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`):

```json
{
    "mcpServers": {
        "proxmox": {
            "command": "uv",
            "args": ["run", "--directory", "/path/to/ProxmoxMCP", "proxmox-mcp"],
            "env": {
                "PROXMOX_MCP_CONFIG": "/path/to/ProxmoxMCP/proxmox-config/config.json"
            }
        }
    }
}
```

# 🔧 Available Tools

The server provides the following MCP tools for interacting with Proxmox:

### get_nodes
Lists all nodes in the Proxmox cluster.

- Parameters: None
- Example Response:
  ```
  🖥️ Proxmox Nodes

  🖥️ pve-compute-01
    • Status: ONLINE
    • Uptime: ⏳ 156d 12h
    • CPU Cores: 64
    • Memory: 186.5 GB / 512.0 GB (36.4%)

  🖥️ pve-compute-02
    • Status: ONLINE
    • Uptime: ⏳ 156d 11h
    • CPU Cores: 64
    • Memory: 201.3 GB / 512.0 GB (39.3%)
  ```

### get_node_status
Get detailed status of a specific node.

- Parameters:
  - `node` (string, required): Name of the node
- Example Response:
  ```
  🖥️ Node: pve-compute-01
    • Status: ONLINE
    • Uptime: ⏳ 156d 12h
    • CPU Usage: 42.3%
    • CPU Cores: 64 (AMD EPYC 7763)
    • Memory: 186.5 GB / 512.0 GB (36.4%)
    • Network: ⬆️ 12.8 GB/s ⬇️ 9.2 GB/s
    • Temperature: 38°C
  ```

### get_vms
List all VMs across the cluster.

- Parameters: None
- Example Response:
  ```
  🗃️ Virtual Machines

  🗃️ prod-db-master (ID: 100)
    • Status: RUNNING
    • Node: pve-compute-01
    • CPU Cores: 16
    • Memory: 92.3 GB / 128.0 GB (72.1%)

  🗃️ prod-web-01 (ID: 102)
    • Status: RUNNING
    • Node: pve-compute-01
    • CPU Cores: 8
    • Memory: 12.8 GB / 32.0 GB (40.0%)
  ```

### get_storage
List available storage.

- Parameters: None
- Example Response:
  ```
  💾 Storage Pools

  💾 ceph-prod
    • Status: ONLINE
    • Type: rbd
    • Usage: 12.8 TB / 20.0 TB (64.0%)
    • IOPS: ⬆️ 15.2k ⬇️ 12.8k

  💾 local-zfs
    • Status: ONLINE
    • Type: zfspool
    • Usage: 3.2 TB / 8.0 TB (40.0%)
    • IOPS: ⬆️ 42.8k ⬇️ 35.6k
  ```

### get_cluster_status
Get overall cluster status.

- Parameters: None
- Example Response:
  ```
  ⚙️ Proxmox Cluster

    • Name: enterprise-cloud
    • Status: HEALTHY
    • Quorum: OK
    • Nodes: 4 ONLINE
    • Version: 8.1.3
    • HA Status: ACTIVE
    • Resources:
      - Total CPU Cores: 192
      - Total Memory: 1536 GB
      - Total Storage: 70 TB
    • Workload:
      - Running VMs: 7
      - Total VMs: 8
      - Average CPU Usage: 38.6%
      - Average Memory Usage: 42.8%
  ```

### execute_vm_command
Execute a command in a VM's console using QEMU Guest Agent.

- Parameters:
  - `node` (string, required): Name of the node where VM is running
  - `vmid` (string, required): ID of the VM
  - `command` (string, required): Command to execute
- Example Response:
  ```
  🔧 Console Command Result
    • Status: SUCCESS
    • Command: systemctl status nginx
    • Node: pve-compute-01
    • VM: prod-web-01 (ID: 102)

  Output:
  ● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)
     Active: active (running) since Tue 2025-02-18 15:23:45 UTC; 2 months 3 days ago
  ```
- Requirements:
  - VM must be running
  - QEMU Guest Agent must be installed and running in the VM
  - Command execution permissions must be enabled in the Guest Agent
- Error Handling:
  - Returns error if VM is not running
  - Returns error if VM is not found
  - Returns error if command execution fails
  - Includes command output even if command returns non-zero exit code

## 👨‍💻 Development

After activating your virtual environment:

- Run tests: `pytest`
- Format code: `black .`
- Type checking: `mypy .`
- Lint: `ruff .`

## 📁 Project Structure

```
proxmox-mcp/
├── src/
│   └── proxmox_mcp/
│       ├── server.py          # Main MCP server implementation
│       ├── config/            # Configuration handling
│       ├── core/              # Core functionality
│       ├── formatting/        # Output formatting and themes
│       ├── tools/             # Tool implementations
│       │   └── console/       # VM console operations
│       └── utils/             # Utilities (auth, logging)
├── tests/                     # Test suite
├── proxmox-config/
│   └── config.example.json    # Configuration template
├── pyproject.toml            # Project metadata and dependencies
└── LICENSE                   # MIT License
```

## 📄 License

MIT License

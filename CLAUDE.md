# ProxmoxMCP — Claude Code Guide

## Project Overview

Python MCP (Model Context Protocol) server that exposes Proxmox hypervisor management as tools for AI assistants. Connects to multiple Proxmox clusters via their REST API using token-based auth.

## Environment Setup

```bash
# Activate the virtual environment (uses venv/, not .venv/)
source ~/ProxmoxMCP/venv/bin/activate

# Run the server
PROXMOX_MCP_CONFIG=~/ProxmoxMCP/proxmox-config/config.json python -m proxmox_mcp.server
```

## Development Commands

```bash
source venv/bin/activate

pytest                  # run tests
black .                 # format code
ruff .                  # lint
mypy .                  # type check
```

## Architecture

```
src/proxmox_mcp/
├── server.py           # FastMCP server, tool registration, entry point
├── config/
│   ├── loader.py       # loads config.json, validates with Pydantic
│   └── models.py       # Pydantic config models (ClusterConfig, etc.)
├── core/
│   ├── proxmox.py      # ProxmoxClusterManager — manages N cluster connections
│   └── logging.py      # logging setup
├── tools/
│   ├── base.py         # shared tool base class
│   ├── definitions.py  # MCP tool description strings
│   ├── node.py         # get_nodes, get_node_status
│   ├── vm.py           # get_vms, execute_vm_command (async, uses QEMU Guest Agent)
│   ├── storage.py      # get_storage
│   ├── cluster.py      # get_cluster_status
│   └── console/        # VM console command execution
│       └── manager.py
├── formatting/         # Rich output formatting with themes
│   ├── formatters.py
│   ├── theme.py
│   ├── templates.py
│   ├── components.py
│   └── colors.py
└── utils/
    ├── auth.py         # token auth helpers
    └── logging.py
```

## Configuration

Config lives at `proxmox-config/config.json`. Multi-cluster format — each cluster has its own name, host, and auth token:

```json
{
    "clusters": [
        {
            "name": "Building 1-ABE",
            "proxmox": { "host": "10.8.0.200", "port": 8006, "verify_ssl": false, "service": "PVE" },
            "auth": { "user": "root@pam", "token_name": "mcp-token", "token_value": "..." }
        }
    ],
    "logging": { "level": "DEBUG", "format": "...", "file": "proxmox_mcp.log" }
}
```

Four configured clusters: Building 1-ABE (10.8.0.200), Building 2 (10.8.64.200), Building 3 (10.8.128.200), Building 4 (10.8.192.200).

**Do not commit `proxmox-config/config.json`** — it contains real API tokens.

## MCP Tools

All tools require a `cluster` parameter (e.g. `"Building 1-ABE"`):

| Tool | Description |
|------|-------------|
| `list_clusters` | List available cluster names |
| `get_nodes` | List nodes in a cluster |
| `get_node_status` | Detailed status of a specific node |
| `get_vms` | List all VMs in a cluster |
| `execute_vm_command` | Run shell command via QEMU Guest Agent |
| `get_storage` | List storage pools |
| `get_cluster_status` | Overall cluster health/stats |

## Key Patterns

- All tool functions are registered via `@self.mcp.tool(description=...)` decorators in `server.py:_setup_tools()`
- `execute_vm_command` is async; all other tools are sync
- `ProxmoxClusterManager` in `core/proxmox.py` is the central connection object passed to all tool classes
- Output formatting uses the `formatting/` module — rich text with emoji icons and themed components

## Tests

```bash
pytest tests/test_server.py
pytest tests/test_vm_console.py
```

`asyncio_mode = "strict"` is set in pyproject.toml — async tests must use `@pytest.mark.asyncio`.

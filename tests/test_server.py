"""
Tests for the Proxmox MCP server.
"""

import json
import pytest
from unittest.mock import Mock, patch

from mcp.server.fastmcp.exceptions import ToolError
from proxmox_mcp.server import ProxmoxMCPServer


@pytest.fixture
def config_path(tmp_path):
    config = {
        "clusters": [{
            "name": "test-cluster",
            "proxmox": {"host": "test.proxmox.com", "port": 8006, "verify_ssl": False, "service": "PVE"},
            "auth": {"user": "test@pve", "token_name": "test_token", "token_value": "test_value"}
        }],
        "logging": {"level": "DEBUG"}
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(config))
    return str(p)


@pytest.fixture
def mock_api():
    api = Mock()
    api.nodes.get.return_value = [{"node": "pve1", "status": "online"}]
    api.nodes.return_value.status.get.return_value = {
        "uptime": 86400,
        "cpuinfo": {"cpus": 4},
        "memory": {"used": 1_000_000_000, "total": 4_000_000_000},
    }
    api.nodes.return_value.qemu.get.return_value = [
        {"vmid": "100", "name": "vm1", "status": "running", "mem": 500_000_000, "maxmem": 2_000_000_000}
    ]
    api.nodes.return_value.qemu.return_value.config.get.return_value = {"cores": 2}
    api.storage.get.return_value = [
        {"storage": "local", "type": "dir", "enabled": True}
    ]
    api.nodes.return_value.storage.return_value.status.get.return_value = {
        "used": 10_000_000_000,
        "total": 50_000_000_000,
        "avail": 40_000_000_000,
    }
    api.cluster.status.get.return_value = [
        {"type": "cluster", "name": "test-cluster", "quorate": 1}
    ]
    return api


@pytest.fixture
def mock_cluster_manager(mock_api):
    manager = Mock()
    manager.list_clusters.return_value = ["test-cluster"]
    manager.get_api.return_value = mock_api
    return manager


@pytest.fixture
def server(config_path, mock_cluster_manager):
    with patch("proxmox_mcp.server.ProxmoxClusterManager", return_value=mock_cluster_manager):
        return ProxmoxMCPServer(config_path)


def test_server_initialization(server):
    cluster = server.config.clusters[0]
    assert cluster.proxmox.host == "test.proxmox.com"
    assert cluster.auth.user == "test@pve"
    assert cluster.auth.token_name == "test_token"
    assert cluster.auth.token_value == "test_value"
    assert server.config.logging.level == "DEBUG"


@pytest.mark.asyncio
async def test_list_tools(server):
    tools = await server.mcp.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "list_clusters" in tool_names
    assert "get_nodes" in tool_names
    assert "get_node_status" in tool_names
    assert "get_vms" in tool_names
    assert "execute_vm_command" in tool_names
    assert "get_storage" in tool_names
    assert "get_cluster_status" in tool_names


@pytest.mark.asyncio
async def test_list_clusters(server):
    response = await server.mcp.call_tool("list_clusters", {})
    assert len(response) > 0
    assert "test-cluster" in response[0].text


@pytest.mark.asyncio
async def test_get_nodes(server, mock_api):
    response = await server.mcp.call_tool("get_nodes", {"cluster": "test-cluster"})
    assert len(response) > 0
    assert "pve1" in response[0].text


@pytest.mark.asyncio
async def test_get_node_status_missing_parameter(server):
    with pytest.raises(ToolError):
        await server.mcp.call_tool("get_node_status", {"cluster": "test-cluster"})


@pytest.mark.asyncio
async def test_get_node_status(server, mock_api):
    response = await server.mcp.call_tool(
        "get_node_status", {"cluster": "test-cluster", "node": "pve1"}
    )
    assert len(response) > 0
    assert "pve1" in response[0].text


@pytest.mark.asyncio
async def test_get_vms(server, mock_api):
    response = await server.mcp.call_tool("get_vms", {"cluster": "test-cluster"})
    assert len(response) > 0
    assert "vm1" in response[0].text


@pytest.mark.asyncio
async def test_get_storage(server, mock_api):
    response = await server.mcp.call_tool("get_storage", {"cluster": "test-cluster"})
    assert len(response) > 0
    assert "local" in response[0].text


@pytest.mark.asyncio
async def test_get_cluster_status(server, mock_api):
    response = await server.mcp.call_tool("get_cluster_status", {"cluster": "test-cluster"})
    assert len(response) > 0


@pytest.mark.asyncio
async def test_execute_vm_command_missing_parameters(server):
    with pytest.raises(ToolError):
        await server.mcp.call_tool("execute_vm_command", {})

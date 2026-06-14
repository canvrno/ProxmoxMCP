"""
Tests for VM console operations.
"""

import pytest
from unittest.mock import Mock

from proxmox_mcp.tools.console.manager import VMConsoleManager


@pytest.fixture(autouse=True)
def patch_sleep(monkeypatch):
    async def fast_sleep(_):
        pass
    monkeypatch.setattr("asyncio.sleep", fast_sleep)


@pytest.fixture
def mock_proxmox():
    mock = Mock()
    mock.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }

    exec_endpoint = Mock()
    exec_endpoint.post.return_value = {"pid": 123}

    exec_status_endpoint = Mock()
    exec_status_endpoint.get.return_value = {
        "out-data": "command output",
        "err-data": "",
        "exitcode": 0,
        "exited": 1,
    }

    mock.nodes.return_value.qemu.return_value.agent.side_effect = (
        lambda name: exec_endpoint if name == "exec" else exec_status_endpoint
    )
    return mock


@pytest.fixture
def mock_cluster_manager(mock_proxmox):
    manager = Mock()
    manager.get_api.return_value = mock_proxmox
    return manager


@pytest.fixture
def vm_console(mock_cluster_manager):
    return VMConsoleManager(mock_cluster_manager)


@pytest.mark.asyncio
async def test_execute_command_success(vm_console):
    result = await vm_console.execute_command("test-cluster", "node1", "100", "ls -l")
    assert result["success"] is True
    assert result["output"] == "command output"
    assert result["error"] == ""
    assert result["exit_code"] == 0


@pytest.mark.asyncio
async def test_execute_command_vm_not_running(vm_console, mock_proxmox):
    mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "stopped"
    }
    with pytest.raises(ValueError, match="not running"):
        await vm_console.execute_command("test-cluster", "node1", "100", "ls -l")


@pytest.mark.asyncio
async def test_execute_command_vm_not_found(vm_console, mock_proxmox):
    mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = (
        Exception("VM not found")
    )
    with pytest.raises(ValueError, match="not found"):
        await vm_console.execute_command("test-cluster", "node1", "100", "ls -l")


@pytest.mark.asyncio
async def test_execute_command_failure(vm_console, mock_proxmox):
    failing_exec = Mock()
    failing_exec.post.side_effect = Exception("Command failed")
    mock_proxmox.nodes.return_value.qemu.return_value.agent.side_effect = (
        lambda name: failing_exec
    )
    with pytest.raises(RuntimeError, match="Failed to execute command"):
        await vm_console.execute_command("test-cluster", "node1", "100", "ls -l")


@pytest.mark.asyncio
async def test_execute_command_with_error_output(vm_console, mock_proxmox):
    exec_endpoint = Mock()
    exec_endpoint.post.return_value = {"pid": 456}

    exec_status_endpoint = Mock()
    exec_status_endpoint.get.return_value = {
        "out-data": "",
        "err-data": "command error",
        "exitcode": 1,
        "exited": 1,
    }

    mock_proxmox.nodes.return_value.qemu.return_value.agent.side_effect = (
        lambda name: exec_endpoint if name == "exec" else exec_status_endpoint
    )

    result = await vm_console.execute_command("test-cluster", "node1", "100", "invalid-command")
    assert result["success"] is True
    assert result["output"] == ""
    assert result["error"] == "command error"
    assert result["exit_code"] == 1

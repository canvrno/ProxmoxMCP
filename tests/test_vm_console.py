"""
Tests for VM console operations.
"""

import asyncio
import pytest
from unittest.mock import Mock

from proxmox_mcp.tools.vm_console import VMConsoleManager


@pytest.fixture
def mock_proxmox():
    """Fixture to create a mock ProxmoxAPI instance."""
    mock = Mock()
    mock.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }

    exec_endpoint = Mock()
    exec_endpoint.post.return_value = {"pid": 123}

    status_endpoint = Mock()
    status_endpoint.get.return_value = {
        "out-data": "command output",
        "err-data": "",
        "exitcode": 0,
        "exited": 1,
    }

    def agent_endpoint(name):
        if name == "exec":
            return exec_endpoint
        if name == "exec-status":
            return status_endpoint
        raise AssertionError(f"Unexpected guest-agent endpoint: {name}")

    mock.nodes.return_value.qemu.return_value.agent.side_effect = agent_endpoint
    mock.exec_endpoint = exec_endpoint
    mock.exec_status_endpoint = status_endpoint
    return mock


@pytest.fixture
def vm_console(mock_proxmox):
    """Fixture to create a VMConsoleManager instance."""
    return VMConsoleManager(mock_proxmox)


def test_execute_command_success(vm_console, mock_proxmox):
    """Test successful command execution."""
    result = asyncio.run(vm_console.execute_command("node1", "100", "ls -l"))

    assert result["success"] is True
    assert result["output"] == "command output"
    assert result["error"] == ""
    assert result["exit_code"] == 0

    # Verify correct API calls
    mock_proxmox.nodes.assert_called_with("node1")
    mock_proxmox.nodes.return_value.qemu.assert_called_with("100")
    mock_proxmox.exec_endpoint.post.assert_called_with(command="ls -l")
    mock_proxmox.exec_status_endpoint.get.assert_called_with(pid=123)

def test_execute_command_vm_not_running(vm_console, mock_proxmox):
    """Test command execution on stopped VM."""
    mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "stopped"
    }

    with pytest.raises(ValueError, match="not running"):
        asyncio.run(vm_console.execute_command("node1", "100", "ls -l"))

def test_execute_command_vm_not_found(vm_console, mock_proxmox):
    """Test command execution on non-existent VM."""
    mock_proxmox.nodes.return_value.qemu.return_value.status.current.get.side_effect = \
        Exception("VM not found")

    with pytest.raises(ValueError, match="not found"):
        asyncio.run(vm_console.execute_command("node1", "100", "ls -l"))

def test_execute_command_failure(vm_console, mock_proxmox):
    """Test command execution failure."""
    mock_proxmox.exec_endpoint.post.side_effect = Exception("Command failed")

    with pytest.raises(RuntimeError, match="Failed to execute command"):
        asyncio.run(vm_console.execute_command("node1", "100", "ls -l"))

def test_execute_command_with_error_output(vm_console, mock_proxmox):
    """Test command execution with error output."""
    mock_proxmox.exec_status_endpoint.get.return_value = {
        "out-data": "",
        "err-data": "command error",
        "exitcode": 1,
        "exited": 1,
    }

    result = asyncio.run(vm_console.execute_command("node1", "100", "invalid-command"))

    assert result["success"] is True  # Success refers to API call, not command
    assert result["output"] == ""
    assert result["error"] == "command error"
    assert result["exit_code"] == 1

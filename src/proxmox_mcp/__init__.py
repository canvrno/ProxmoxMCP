"""
Proxmox MCP Server - A Model Context Protocol server for interacting with Proxmox hypervisors.
"""

from typing import TYPE_CHECKING

__version__ = "0.1.0"
__all__ = ["ProxmoxMCPServer"]

if TYPE_CHECKING:
    from .server import ProxmoxMCPServer


def __getattr__(name):
    if name == "ProxmoxMCPServer":
        from .server import ProxmoxMCPServer

        return ProxmoxMCPServer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

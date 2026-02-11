"""
LXC container tools for Proxmox MCP.

This module provides tools for managing and interacting with Proxmox LXC containers:
- Listing all containers across the cluster with their status
- Retrieving detailed container information including:
  * Resource allocation (CPU, memory)
  * Runtime status
  * Node placement
"""
from typing import List
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .definitions import GET_CONTAINERS_DESC


class LXCTools(ProxmoxTool):
    """Tools for managing Proxmox LXC containers.

    Provides functionality for:
    - Retrieving cluster-wide container information
    - Getting detailed container status and configuration

    Implements fallback mechanisms for scenarios where detailed
    container information might be temporarily unavailable.
    """

    def get_containers(self) -> List[Content]:
        """List all LXC containers across the cluster with detailed status.

        Retrieves comprehensive information for each container including:
        - Basic identification (ID, name)
        - Runtime status (running, stopped)
        - Resource allocation and usage:
          * CPU cores
          * Memory allocation and usage
        - Node placement

        Implements a fallback mechanism that returns basic information
        if detailed configuration retrieval fails for any container.

        Returns:
            List of Content objects containing formatted container information:
            {
                "vmid": "200",
                "name": "container-name",
                "status": "running/stopped",
                "node": "node-name",
                "cpus": core_count,
                "memory": {
                    "used": bytes,
                    "total": bytes
                }
            }

        Raises:
            RuntimeError: If the cluster-wide container query fails
        """
        try:
            result = []
            for node in self.proxmox.nodes.get():
                node_name = node["node"]
                containers = self.proxmox.nodes(node_name).lxc.get()
                for ct in containers:
                    vmid = ct["vmid"]
                    # Get container config for CPU cores
                    try:
                        config = self.proxmox.nodes(node_name).lxc(vmid).config.get()
                        result.append({
                            "vmid": vmid,
                            "name": ct.get("name", f"CT{vmid}"),
                            "status": ct["status"],
                            "node": node_name,
                            "cpus": config.get("cores", 1),
                            "memory": {
                                "used": ct.get("mem", 0),
                                "total": ct.get("maxmem", 0)
                            }
                        })
                    except Exception:
                        # Fallback if can't get config
                        result.append({
                            "vmid": vmid,
                            "name": ct.get("name", f"CT{vmid}"),
                            "status": ct["status"],
                            "node": node_name,
                            "cpus": "N/A",
                            "memory": {
                                "used": ct.get("mem", 0),
                                "total": ct.get("maxmem", 0)
                            }
                        })
            return self._format_response(result, "containers")
        except Exception as e:
            self._handle_error("get containers", e)

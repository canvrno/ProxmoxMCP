"""
LXC container tools for Proxmox MCP.
"""
from typing import List
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class ContainerTools(ProxmoxTool):
    """Tools for managing Proxmox LXC containers."""

    def get_containers(self) -> List[Content]:
        """List all LXC containers across the cluster with status and resource usage."""
        try:
            result = []
            for node in self.proxmox.nodes.get():
                node_name = node["node"]
                containers = self.proxmox.nodes(node_name).lxc.get()
                for ct in containers:
                    vmid = ct["vmid"]
                    try:
                        config = self.proxmox.nodes(node_name).lxc(vmid).config.get()
                        cpus = config.get("cores", config.get("cpulimit", "N/A"))
                    except Exception:
                        cpus = "N/A"
                    result.append({
                        "vmid": vmid,
                        "name": ct.get("name", f"CT {vmid}"),
                        "status": ct["status"],
                        "node": node_name,
                        "cpus": cpus,
                        "memory": {
                            "used": ct.get("mem", 0),
                            "total": ct.get("maxmem", 0)
                        }
                    })
            return self._format_response(result, "containers")
        except Exception as e:
            self._handle_error("get containers", e)

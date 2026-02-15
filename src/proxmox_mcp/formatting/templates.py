"""
Output templates for Proxmox MCP resource types.
"""
from typing import Dict, List, Any
from .formatters import ProxmoxFormatters
from .theme import ProxmoxTheme
from .colors import ProxmoxColors
from .components import ProxmoxComponents

class ProxmoxTemplates:
    """Output templates for different Proxmox resource types."""
    
    @staticmethod
    def node_list(nodes: List[Dict[str, Any]]) -> str:
        """Template for node list output.
        
        Args:
            nodes: List of node data dictionaries
            
        Returns:
            Formatted node list string
        """
        result = [f"{ProxmoxTheme.RESOURCES['node']} Proxmox Nodes"]
        
        for node in nodes:
            # Get node status
            status = node.get("status", "unknown")
            
            # Get memory info
            memory = node.get("memory", {})
            memory_used = memory.get("used", 0)
            memory_total = memory.get("total", 0)
            memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0
            
            # Format node info
            result.extend([
                "",  # Empty line between nodes
                f"{ProxmoxTheme.RESOURCES['node']} {node['node']}",
                f"  • Status: {status.upper()}",
                f"  • Uptime: {ProxmoxFormatters.format_uptime(node.get('uptime', 0))}",
                f"  • CPU Cores: {node.get('maxcpu', 'N/A')}",
                f"  • Memory: {ProxmoxFormatters.format_bytes(memory_used)} / "
                f"{ProxmoxFormatters.format_bytes(memory_total)} ({memory_percent:.1f}%)"
            ])
            
            # Add disk usage if available
            disk = node.get("disk", {})
            if disk:
                disk_used = disk.get("used", 0)
                disk_total = disk.get("total", 0)
                disk_percent = (disk_used / disk_total * 100) if disk_total > 0 else 0
                result.append(
                    f"  • Disk: {ProxmoxFormatters.format_bytes(disk_used)} / "
                    f"{ProxmoxFormatters.format_bytes(disk_total)} ({disk_percent:.1f}%)"
                )
            
        return "\n".join(result)
    
    @staticmethod
    def node_status(node: str, status: Dict[str, Any]) -> str:
        """Template for detailed node status output.
        
        Args:
            node: Node name
            status: Node status data
            
        Returns:
            Formatted node status string
        """
        memory = status.get("memory", {})
        memory_used = memory.get("used", 0)
        memory_total = memory.get("total", 0)
        memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0
        
        result = [
            f"{ProxmoxTheme.RESOURCES['node']} Node: {node}",
            f"  • Status: {status.get('status', 'unknown').upper()}",
            f"  • Uptime: {ProxmoxFormatters.format_uptime(status.get('uptime', 0))}",
            f"  • CPU Cores: {status.get('maxcpu', 'N/A')}",
            f"  • Memory: {ProxmoxFormatters.format_bytes(memory_used)} / "
            f"{ProxmoxFormatters.format_bytes(memory_total)} ({memory_percent:.1f}%)"
        ]
        
        # Add disk usage if available
        disk = status.get("disk", {})
        if disk:
            disk_used = disk.get("used", 0)
            disk_total = disk.get("total", 0)
            disk_percent = (disk_used / disk_total * 100) if disk_total > 0 else 0
            result.append(
                f"  • Disk: {ProxmoxFormatters.format_bytes(disk_used)} / "
                f"{ProxmoxFormatters.format_bytes(disk_total)} ({disk_percent:.1f}%)"
            )
        
        return "\n".join(result)
    
    @staticmethod
    def vm_list(vms: List[Dict[str, Any]]) -> str:
        """Template for VM list output.
        
        Args:
            vms: List of VM data dictionaries
            
        Returns:
            Formatted VM list string
        """
        result = [f"{ProxmoxTheme.RESOURCES['vm']} Virtual Machines"]
        
        for vm in vms:
            memory = vm.get("memory", {})
            memory_used = memory.get("used", 0)
            memory_total = memory.get("total", 0)
            memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0
            
            result.extend([
                "",  # Empty line between VMs
                f"{ProxmoxTheme.RESOURCES['vm']} {vm['name']} (ID: {vm['vmid']})",
                f"  • Status: {vm['status'].upper()}",
                f"  • Node: {vm['node']}",
                f"  • CPU Cores: {vm.get('cpus', 'N/A')}",
                f"  • Memory: {ProxmoxFormatters.format_bytes(memory_used)} / "
                f"{ProxmoxFormatters.format_bytes(memory_total)} ({memory_percent:.1f}%)"
            ])
            
        return "\n".join(result)
    
    @staticmethod
    def storage_list(storage: List[Dict[str, Any]]) -> str:
        """Template for storage list output.
        
        Args:
            storage: List of storage data dictionaries
            
        Returns:
            Formatted storage list string
        """
        result = [f"{ProxmoxTheme.RESOURCES['storage']} Storage Pools"]
        
        for store in storage:
            used = store.get("used", 0)
            total = store.get("total", 0)
            percent = (used / total * 100) if total > 0 else 0
            
            result.extend([
                "",  # Empty line between storage pools
                f"{ProxmoxTheme.RESOURCES['storage']} {store['storage']}",
                f"  • Status: {store.get('status', 'unknown').upper()}",
                f"  • Type: {store['type']}",
                f"  • Usage: {ProxmoxFormatters.format_bytes(used)} / "
                f"{ProxmoxFormatters.format_bytes(total)} ({percent:.1f}%)"
            ])
            
        return "\n".join(result)
    
    @staticmethod
    def container_list(containers: List[Dict[str, Any]]) -> str:
        """Template for container list output.
        
        Args:
            containers: List of container data dictionaries
            
        Returns:
            Formatted container list string
        """
        if not containers:
            return f"{ProxmoxTheme.RESOURCES['container']} No containers found"
            
        result = [f"{ProxmoxTheme.RESOURCES['container']} Containers"]
        
        for container in containers:
            memory = container.get("memory", {})
            memory_used = memory.get("used", 0)
            memory_total = memory.get("total", 0)
            memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0
            
            result.extend([
                "",  # Empty line between containers
                f"{ProxmoxTheme.RESOURCES['container']} {container['name']} (ID: {container['vmid']})",
                f"  • Status: {container['status'].upper()}",
                f"  • Node: {container['node']}",
                f"  • CPU Cores: {container.get('cpus', 'N/A')}",
                f"  • Memory: {ProxmoxFormatters.format_bytes(memory_used)} / "
                f"{ProxmoxFormatters.format_bytes(memory_total)} ({memory_percent:.1f}%)"
            ])
            
        return "\n".join(result)

    @staticmethod
    def cluster_status(status: Dict[str, Any]) -> str:
        """Template for cluster status output.
        
        Args:
            status: Cluster status data
            
        Returns:
            Formatted cluster status string
        """
        result = [f"{ProxmoxTheme.SECTIONS['configuration']} Proxmox Cluster"]
        
        # Basic cluster info
        result.extend([
            "",
            f"  • Name: {status.get('name', 'N/A')}",
            f"  • Quorum: {'OK' if status.get('quorum') else 'NOT OK'}",
            f"  • Nodes: {status.get('nodes', 0)}",
        ])
        
        # Add resource count if available
        resources = status.get('resources', [])
        if resources:
            result.append(f"  • Resources: {len(resources)}")

        return "\n".join(result)

    @staticmethod
    def network_interfaces(data: List[Dict[str, Any]]) -> str:
        """Template for VM network interfaces output.

        Args:
            data: List of VM data dictionaries with interfaces

        Returns:
            Formatted network interfaces string
        """
        if not data:
            return f"{ProxmoxTheme.RESOURCES['network']} No network interfaces found"

        result = [f"{ProxmoxTheme.RESOURCES['network']} VM Network Interfaces"]

        for vm in data:
            result.extend([
                "",
                f"{ProxmoxTheme.RESOURCES['vm']} {vm.get('name', 'Unknown')} (ID: {vm['vmid']}) on {vm['node']}"
            ])

            if vm.get("error"):
                result.append(f"    ⚠️ Error: {vm['error']}")
                continue

            interfaces = vm.get("interfaces", [])
            if not interfaces:
                result.append("    No interfaces found")
                continue

            for iface in interfaces:
                result.extend([
                    f"    {iface.get('name', 'unknown')}",
                    f"      • MAC: {iface.get('mac', 'N/A')}"
                ])
                if iface.get("ipv4"):
                    result.append(f"      • IPv4: {', '.join(iface['ipv4'])}")
                if iface.get("ipv6"):
                    result.append(f"      • IPv6: {', '.join(iface['ipv6'])}")

        return "\n".join(result)

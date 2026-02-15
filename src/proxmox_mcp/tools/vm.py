"""
VM-related tools for Proxmox MCP.

This module provides tools for managing and interacting with Proxmox VMs:
- Listing all VMs across the cluster with their status
- Retrieving detailed VM information including:
  * Resource allocation (CPU, memory)
  * Runtime status
  * Node placement
- Executing commands within VMs via QEMU guest agent
- Handling VM console operations

The tools implement fallback mechanisms for scenarios where
detailed VM information might be temporarily unavailable.
"""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .definitions import GET_VMS_DESC, EXECUTE_VM_COMMAND_DESC, GET_VM_NETWORK_INTERFACES_DESC
from .console.manager import VMConsoleManager

class VMTools(ProxmoxTool):
    """Tools for managing Proxmox VMs.
    
    Provides functionality for:
    - Retrieving cluster-wide VM information
    - Getting detailed VM status and configuration
    - Executing commands within VMs
    - Managing VM console operations
    
    Implements fallback mechanisms for scenarios where detailed
    VM information might be temporarily unavailable. Integrates
    with QEMU guest agent for VM command execution.
    """

    def __init__(self, proxmox_api):
        """Initialize VM tools.

        Args:
            proxmox_api: Initialized ProxmoxAPI instance
        """
        super().__init__(proxmox_api)
        self.console_manager = VMConsoleManager(proxmox_api)

    def get_vms(self) -> List[Content]:
        """List all virtual machines across the cluster with detailed status.

        Retrieves comprehensive information for each VM including:
        - Basic identification (ID, name)
        - Runtime status (running, stopped)
        - Resource allocation and usage:
          * CPU cores
          * Memory allocation and usage
        - Node placement
        
        Implements a fallback mechanism that returns basic information
        if detailed configuration retrieval fails for any VM.

        Returns:
            List of Content objects containing formatted VM information:
            {
                "vmid": "100",
                "name": "vm-name",
                "status": "running/stopped",
                "node": "node-name",
                "cpus": core_count,
                "memory": {
                    "used": bytes,
                    "total": bytes
                }
            }

        Raises:
            RuntimeError: If the cluster-wide VM query fails
        """
        try:
            result = []
            for node in self.proxmox.nodes.get():
                node_name = node["node"]
                vms = self.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    vmid = vm["vmid"]
                    # Get VM config for CPU cores
                    try:
                        config = self.proxmox.nodes(node_name).qemu(vmid).config.get()
                        result.append({
                            "vmid": vmid,
                            "name": vm["name"],
                            "status": vm["status"],
                            "node": node_name,
                            "cpus": config.get("cores", "N/A"),
                            "memory": {
                                "used": vm.get("mem", 0),
                                "total": vm.get("maxmem", 0)
                            }
                        })
                    except Exception:
                        # Fallback if can't get config
                        result.append({
                            "vmid": vmid,
                            "name": vm["name"],
                            "status": vm["status"],
                            "node": node_name,
                            "cpus": "N/A",
                            "memory": {
                                "used": vm.get("mem", 0),
                                "total": vm.get("maxmem", 0)
                            }
                        })
            return self._format_response(result, "vms")
        except Exception as e:
            self._handle_error("get VMs", e)

    async def execute_command(self, node: str, vmid: str, command: str) -> List[Content]:
        """Execute a command in a VM via QEMU guest agent.

        Uses the QEMU guest agent to execute commands within a running VM.
        Requires:
        - VM must be running
        - QEMU guest agent must be installed and running in the VM
        - Command execution permissions must be enabled

        Args:
            node: Host node name (e.g., 'pve1', 'proxmox-node2')
            vmid: VM ID number (e.g., '100', '101')
            command: Shell command to run (e.g., 'uname -a', 'systemctl status nginx')

        Returns:
            List of Content objects containing formatted command output:
            {
                "success": true/false,
                "output": "command output",
                "error": "error message if any"
            }

        Raises:
            ValueError: If VM is not found, not running, or guest agent is not available
            RuntimeError: If command execution fails due to permissions or other issues
        """
        try:
            result = await self.console_manager.execute_command(node, vmid, command)
            # Use the command output formatter from ProxmoxFormatters
            from ..formatting import ProxmoxFormatters
            formatted = ProxmoxFormatters.format_command_output(
                success=result["success"],
                command=command,
                output=result["output"],
                error=result.get("error")
            )
            return [Content(type="text", text=formatted)]
        except Exception as e:
            self._handle_error(f"execute command on VM {vmid}", e)

    def get_vm_network_interfaces(
        self,
        targets: Optional[List[dict]] = None,
        node: Optional[str] = None,
        vmid: Optional[str] = None
    ) -> List[Content]:
        """Get network interface information for VM(s) via QEMU guest agent.

        Uses the guest agent's network-get-interfaces capability to retrieve
        IP addresses and MAC addresses. This does not require guest-exec
        permissions, only the basic guest agent to be running.

        Args:
            targets: List of VM targets [{"node": "pve1", "vmid": "100"}, ...]. Takes priority.
            node: Host node name (e.g., 'pve1'). If omitted, queries all nodes.
            vmid: VM ID number (e.g., '100'). If omitted, queries all running VMs.

        Returns:
            List of Content objects containing formatted network interface info

        Raises:
            ValueError: If VM is not found or not running
            RuntimeError: If guest agent query fails
        """
        try:
            results = []

            # targets takes priority if provided
            if targets:
                vm_targets = self._validate_targets(targets)
            else:
                vm_targets = self._get_vm_targets(node, vmid)

            for target_node, target_vmid, vm_name in vm_targets:
                vm_result = {
                    "vmid": target_vmid,
                    "node": target_node,
                    "name": vm_name,
                    "interfaces": [],
                    "error": None
                }

                try:
                    interfaces = self._query_vm_network_interfaces(target_node, target_vmid)
                    vm_result["interfaces"] = interfaces
                except Exception as e:
                    vm_result["error"] = str(e)

                results.append(vm_result)

            return self._format_response(results, "network_interfaces")
        except Exception as e:
            self._handle_error("get network interfaces", e)

    def _get_vm_targets(self, node: Optional[str], vmid: Optional[str]) -> List[tuple]:
        """Get list of (node, vmid, name) tuples to query based on parameters.

        Args:
            node: Host node name, or None for all nodes
            vmid: VM ID, or None for all running VMs

        Returns:
            List of (node, vmid, name) tuples for VMs to query
        """
        targets = []

        if node and vmid:
            # Single VM - get name from API
            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            targets.append((node, vmid, vm_status.get("name", f"VM {vmid}")))
        elif node:
            # All running VMs on specified node
            vms = self.proxmox.nodes(node).qemu.get()
            for vm in vms:
                if vm["status"] == "running":
                    targets.append((node, str(vm["vmid"]), vm.get("name", f"VM {vm['vmid']}")))
        else:
            # All running VMs cluster-wide
            for n in self.proxmox.nodes.get():
                node_name = n["node"]
                vms = self.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    if vm["status"] == "running":
                        targets.append((node_name, str(vm["vmid"]), vm.get("name", f"VM {vm['vmid']}")))

        return targets

    def _validate_targets(self, targets: List[dict]) -> List[tuple]:
        """Validate and convert target list to (node, vmid, name) tuples.

        Args:
            targets: List of dicts with 'node' and 'vmid' keys

        Returns:
            List of (node, vmid, name) tuples

        Raises:
            ValueError: If target format is invalid
        """
        validated = []
        for target in targets:
            if not isinstance(target, dict):
                raise ValueError(f"Target must be dict, got {type(target)}")

            node = target.get('node')
            vmid = target.get('vmid')

            if not node or not vmid:
                raise ValueError(f"Target must have 'node' and 'vmid': {target}")

            # Get VM name from API
            try:
                vm_status = self.proxmox.nodes(str(node)).qemu(str(vmid)).status.current.get()
                validated.append((str(node), str(vmid), vm_status.get("name", f"VM {vmid}")))
            except Exception:
                # Include in results with error rather than failing validation
                validated.append((str(node), str(vmid), f"VM {vmid}"))

        return validated

    def _query_vm_network_interfaces(self, node: str, vmid: str) -> List[dict]:
        """Query a single VM's network interfaces via guest agent.

        Args:
            node: Host node name
            vmid: VM ID number

        Returns:
            List of interface dictionaries with name, mac, ipv4, ipv6

        Raises:
            Exception: If guest agent query fails
        """
        agent_endpoint = self.proxmox.nodes(node).qemu(vmid).agent
        network_data = agent_endpoint("network-get-interfaces").get()

        interfaces = []
        for iface in network_data.get("result", []):
            if iface.get("name") == "lo":
                continue  # Skip loopback

            interface_info = {
                "name": iface.get("name"),
                "mac": iface.get("hardware-address"),
                "ipv4": [],
                "ipv6": []
            }

            for addr in iface.get("ip-addresses", []):
                ip = addr.get("ip-address")
                if addr.get("ip-address-type") == "ipv4":
                    interface_info["ipv4"].append(ip)
                elif addr.get("ip-address-type") == "ipv6":
                    interface_info["ipv6"].append(ip)

            interfaces.append(interface_info)

        return interfaces

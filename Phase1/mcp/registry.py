# MCP Tool Registry — simulates Model Context Protocol tool discovery
# No agent is allowed to call any function/API directly, every tool must be registered here and discovered at runtime via discover(). This enforces the MCP constraint: "no hardcoded APIs"

from typing import Callable, Dict, Any

class MCPRegistry:       #Simulates an MCP (Model Context Protocol) tool registry. In a real MCP setup, tools are discovered from a remote MCP server. Here we simulate that with a local registry that enforces the same architectural principle: agents never call tools directly, they always discover and invoke through this registry.
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, schema: Dict[str, Any], handler: Callable):   # Register a tool with its metadata and handler.
        self._tools[name] = {
            "name": name,
            "description": description,
            "schema": schema,
            "handler": handler
        }
        print(f"[MCP] Tool registered: '{name}'")

    def discover(self, name: str) -> Callable:     #discover a tool by name at runtime.
        if name not in self._tools:
            available = list(self._tools.keys())
            raise ValueError(
                f"[MCP] Tool '{name}' not found in registry.\n"
                f"Available tools: {available}\n"
                f"Register the tool before using it."
            )
        print(f"[MCP] Tool discovered and invoked: '{name}'")
        return self._tools[name]["handler"]

    def list_tools(self) -> list:   #returns all registered tool names(agents can query this)...
        return list(self._tools.keys())

    def get_schema(self, name: str) -> Dict[str, Any]: #returns the input schema for a tool
        if name not in self._tools:
            raise ValueError(f"[MCP] Tool '{name}' not found.")
        return self._tools[name]["schema"]

    def describe(self, name: str) -> str:    #returns the description of a tool
        if name not in self._tools:
            raise ValueError(f"[MCP] Tool '{name}' not found.")
        return self._tools[name]["description"]


# Global singleton registry instance
# All agents import this single instance
mcp_registry = MCPRegistry()
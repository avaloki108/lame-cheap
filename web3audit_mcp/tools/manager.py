"""Tool management for Web3AuditMCP."""
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

class ToolManager:
    """Manages the tools available to the client."""

    def __init__(self, console: Optional[Console] = None, server_connector: Optional[Any] = None):
        self.console = console or Console()
        self.server_connector = server_connector
        self.available_tools: List[Dict[str, Any]] = []
        self.enabled_tools: List[str] = []

    def set_available_tools(self, tools: List[Dict[str, Any]]):
        self.available_tools = tools

    def set_enabled_tools(self, tools: List[str]):
        self.enabled_tools = tools

    def get_enabled_tools(self) -> List[str]:
        return self.enabled_tools

    def get_enabled_tool_objects(self) -> List[Any]:
        # This is a placeholder. In a real implementation, this would return tool objects.
        return []

    def display_available_tools(self):
        self.console.print(Panel("[bold green]Available Tools[/bold green]", border_style="green", expand=False))
        if not self.available_tools:
            self.console.print("No tools available.")
            return

        for i, tool in enumerate(self.available_tools):
            status = "[bold green]enabled[/bold green]" if tool["name"] in self.enabled_tools else "[bold red]disabled[/bold red]"
            self.console.print(f"{i+1}. {tool['name']} - {status}")

    def select_tools(self, clear_console_func=None):
        # This is a placeholder for the interactive tool selection logic.
        self.console.print("[yellow]Tool selection is not yet implemented.[/yellow]")

    def reset_tool_config(self):
        # This is a placeholder for resetting the tool configuration.
        self.enabled_tools = []


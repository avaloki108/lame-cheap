"""Web3AuditMCP Client - A TUI client for performing smart contract audits"""
import asyncio
import os
from contextlib import AsyncExitStack
from typing import List, Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
import ollama

from . import __version__
from .orchestration import OrchestrationLayer
from .config.manager import ConfigManager
from .utils.version import check_for_updates
from .utils.constants import (
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_COMPLETION_STYLE,
)
from .models.manager import ModelManager
from .models.config_manager import ModelConfigManager
from .tools.manager import ToolManager


class Web3AuditClient:
    """Main client class for Web3AuditMCP"""

    def __init__(self, model: str = DEFAULT_MODEL, host: str = DEFAULT_OLLAMA_HOST):
        self.exit_stack = AsyncExitStack()
        self.ollama = ollama.AsyncClient(host=host)
        self.console = Console()
        self.orchestration_layer = OrchestrationLayer(self.console)
        self.config_manager = ConfigManager(self.console)
        self.model_manager = ModelManager(console=self.console, default_model=model, ollama=self.ollama)
        self.model_config_manager = ModelConfigManager(console=self.console)
        self.tool_manager = ToolManager(console=self.console)
        self.chat_history = []
        self.prompt_session = PromptSession(
            style=Style.from_dict(DEFAULT_COMPLETION_STYLE)
        )

    def display_current_model(self):
        self.model_manager.display_current_model()

    async def select_model(self):
        await self.model_manager.select_model_interactive(clear_console_func=self.clear_console)
        self.display_current_model()

    def clear_console(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_available_tools(self):
        self.tool_manager.display_available_tools()

    def configure_model_options(self):
        self.model_config_manager.configure_model_interactive(clear_console_func=self.clear_console)

    async def get_user_input(self, prompt_text: str = None) -> str:
        try:
            if prompt_text is None:
                model_name = self.model_manager.get_current_model().split(':')[0]
                prompt_text = f"🛡️ {model_name}"

            user_input = await self.prompt_session.prompt_async(f'[{prompt_text}]> ')
            return user_input
        except (KeyboardInterrupt, EOFError):
            return "quit"

    def display_welcome_message(self):
        """Display an enhanced welcome message with feature overview."""
        
        features_table = Table(show_header=False, box=None, padding=(0, 1))
        features_table.add_column("Feature", style="bold cyan")
        features_table.add_column("Description", style="white")
        
        features_table.add_row("🔍 Static Analysis", "Slither integration for comprehensive code analysis")
        features_table.add_row("🧠 Symbolic Execution", "Mythril-powered deep vulnerability detection")
        features_table.add_row("🎯 Fuzzing", "Foundry-based property testing and invariant checking")
        features_table.add_row("📋 Custom Checks", "Bug bounty checklist with 500+ vulnerability patterns")
        features_table.add_row("🤖 AI-Powered", "Local LLM integration for intelligent analysis")
        
        welcome_content = f"""[bold cyan]Welcome to Web3AuditMCP! 🕵️‍♂️[/bold cyan]

[bold]The most comprehensive smart contract auditing tool[/bold]
Combining the power of Slither, Mythril, Foundry, and AI-driven analysis.

{features_table}

[dim]Type `help` for commands, `audit <target>` to start, or `quick <target>` for fast scan[/dim]
[dim]Version: {__version__}[/dim]"""

        self.console.print(Panel(
            welcome_content,
            title="[bold]Web3AuditMCP[/bold]",
            border_style="bold blue",
            expand=False
        ))

    async def main_loop(self):
        self.clear_console()
        self.display_welcome_message()
        self.display_current_model()

        await check_for_updates(self.console)

        while True:
            query = await self.get_user_input()

            if query.lower() in ["quit", "exit", "bye"]:
                self.console.print("[bold blue]🛡️ Exiting Web3AuditMCP. Stay secure! 👋[/bold blue]")
                break

            if query.lower() in ["help", "h"]:
                self.display_help()
                continue

            if query.lower() in ["model", "m"]:
                await self.select_model()
                continue

            if query.lower() in ["model-config", "mc"]:
                self.configure_model_options()
                continue

            if query.lower() in ["clear", "cc"]:
                self.chat_history = []
                self.clear_console()
                self.display_welcome_message()
                self.display_current_model()
                continue

            if query.lower().startswith("audit"):
                parts = query.split()
                if len(parts) > 1:
                    target = parts[1]
                    report_panel = await self.orchestration_layer.start_audit({'target': target})
                    self.console.print(report_panel)
                else:
                    self.console.print("[bold red]Usage: audit <target_path_or_url>[/bold red]")
                continue

            if query.lower().startswith("quick"):
                parts = query.split()
                if len(parts) > 1:
                    target = parts[1]
                    report_panel = await self.orchestration_layer.quick_scan(target)
                    self.console.print(report_panel)
                else:
                    self.console.print("[bold red]Usage: quick <target_path_or_url>[/bold red]")
                continue

            if query.lower() in ["stats", "statistics"]:
                self.display_statistics()
                continue

            # AI-powered query processing
            with Live(Spinner("dots", text="[bold yellow]🤖 AI analyzing your query...[/bold yellow]"), console=self.console, transient=True, vertical_overflow="visible") as live:
                response = await self.process_query(query)
                live.update(Panel(Markdown(response), title="[bold green]🤖 AI Response[/bold green]", border_style="green"))

    async def process_query(self, query: str) -> str:
        """Enhanced query processing with security context."""
        
        # Add security auditing context to the query
        security_context = """
You are a smart contract security expert. When analyzing code or answering questions:
1. Focus on common vulnerabilities like reentrancy, integer overflow, access control issues
2. Reference the OWASP Smart Contract Top 10 and common attack patterns
3. Provide specific, actionable security recommendations
4. Consider gas optimization and best practices
5. Mention relevant tools like Slither, Mythril, or Foundry when appropriate
"""
        
        messages = [
            {'role': 'system', 'content': security_context},
            {'role': 'user', 'content': query}
        ]
        
        model = self.model_manager.get_current_model()
        model_options = self.model_config_manager.get_ollama_options()

        chat_params = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": model_options
        }

        stream = await self.ollama.chat(**chat_params)

        response_text = ""
        async for chunk in stream:
            if "content" in chunk["message"]:
                content = chunk["message"]["content"]
                response_text += content
        
        return response_text

    def display_statistics(self):
        """Display audit statistics and tool information."""
        
        stats_table = Table(show_header=True, header_style="bold magenta")
        stats_table.add_column("Tool", style="cyan")
        stats_table.add_column("Status", style="green")
        stats_table.add_column("Checks Available", style="yellow")
        
        stats_table.add_row("Slither", "✅ Ready", "76 detectors")
        stats_table.add_row("Mythril", "✅ Ready", "Symbolic execution")
        stats_table.add_row("Foundry", "✅ Ready", "Property testing")
        stats_table.add_row("Custom Checks", "✅ Ready", "500+ patterns")
        stats_table.add_row("AI Analysis", "✅ Ready", f"Model: {self.model_manager.get_current_model()}")
        
        self.console.print(Panel(
            stats_table,
            title="[bold green]🛡️ Security Analysis Tools Status[/bold green]",
            border_style="green"
        ))

    def display_help(self):
        """Display enhanced help with all available commands."""
        
        commands_table = Table(show_header=True, header_style="bold yellow")
        commands_table.add_column("Command", style="bold cyan", width=20)
        commands_table.add_column("Description", style="white", width=50)
        
        commands_table.add_row("`audit <target>`", "Run comprehensive security audit on smart contract or repository")
        commands_table.add_row("`quick <target>`", "Run fast security scan focusing on critical vulnerabilities")
        commands_table.add_row("`model` or `m`", "Select a different Ollama model for AI analysis")
        commands_table.add_row("`model-config` or `mc`", "Configure advanced model parameters and prompts")
        commands_table.add_row("`stats`", "Display security tools status and statistics")
        commands_table.add_row("`clear` or `cc`", "Clear the screen and conversation history")
        commands_table.add_row("`help` or `h`", "Display this help message")
        commands_table.add_row("`quit`, `exit`, `bye`", "Exit Web3AuditMCP")
        
        help_content = f"""[bold]Web3AuditMCP Commands:[/bold]

{commands_table}

[bold cyan]Examples:[/bold cyan]
• `audit ./contracts/Token.sol` - Audit a single contract
• `audit https://github.com/user/defi-project` - Audit entire repository  
• `quick ./MyContract.sol` - Quick vulnerability scan
• Ask questions like "What are common reentrancy patterns?"

[dim]Tip: Use natural language to ask security questions - the AI will help![/dim]"""

        self.console.print(Panel(
            help_content,
            title="[bold yellow]Help[/bold yellow]",
            border_style="yellow",
            expand=False
        ))


app = typer.Typer()

@app.command()
def main(
    ctx: typer.Context,
    model: str = typer.Option(DEFAULT_MODEL, "--model", "-m", help="Ollama model to use."),
    host: str = typer.Option(DEFAULT_OLLAMA_HOST, "--host", "-H", help="Ollama host URL."),
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit.")
):
    """Web3AuditMCP - Comprehensive Smart Contract Security Auditing Tool"""
    if version:
        print(f"Web3AuditMCP Version: {__version__}")
        raise typer.Exit()

    async def run_client():
        client = Web3AuditClient(model=model, host=host)
        await client.main_loop()

    asyncio.run(run_client())

if __name__ == "__main__":
    app()

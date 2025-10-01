"""Enhanced Web3AuditMCP client with multi-agent system and advanced LLM integration."""

import asyncio
import json
import os
import time
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
import ollama

from .orchestration import EnhancedOrchestrationLayer
from .config.settings import ConfigManager, Web3AuditConfig

class Web3AuditClient:
    """Enhanced Web3AuditMCP client with comprehensive security analysis capabilities."""
    
    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager(self.console)
        self.config = self.config_manager.get_config()
        self.orchestration_layer = EnhancedOrchestrationLayer(self.console)
        
        # Initialize Ollama client
        try:
            self.ollama = ollama.Client()
            self._check_ollama_connection()
        except Exception as e:
            self.console.print(f"[yellow]Warning: Ollama connection failed: {e}[/yellow]")
            self.ollama = None
        
        # Client state
        self.current_session = None
        self.command_history = []
    
    def _check_ollama_connection(self):
        """Check if Ollama is running and accessible."""
        try:
            models = self.ollama.list()
            available_models = [model['name'] for model in models.get('models', [])]
            
            if self.config.model.default_model not in available_models:
                self.console.print(f"[yellow]Warning: Default model '{self.config.model.default_model}' not found[/yellow]")
                if available_models:
                    self.console.print(f"[dim]Available models: {', '.join(available_models[:3])}[/dim]")
                    
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not check Ollama models: {e}[/yellow]")
    
    def display_banner(self):
        """Display the Web3AuditMCP banner and status."""
        
        banner_text = """
╦ ╦┌─┐┌┐ ╔═╗╔═╗┬ ┬┌┬┐┬┌┬┐╔╦╗╔═╗╔═╗
║║║├┤ ├┴┐╠═╣║ ║ ║ │││ │ ║║║║ ║╠═╝
╚╩╝└─┘└─┘╩ ╩╚═╝ ╚═╝─┴┘┴ ┴ ╩ ╩╚═╝╩  
        """
        
        # Create status table
        status_table = Table.grid(padding=1)
        status_table.add_column(style="cyan", justify="right")
        status_table.add_column(style="white")
        
        # Check tool status
        tool_status = asyncio.run(self.orchestration_layer.get_tool_status())
        
        status_table.add_row("🤖 Multi-Agent System:", "[green]ACTIVE[/green]")
        status_table.add_row("🧠 LLM Integration:", "[green]READY[/green]" if self.ollama else "[red]OFFLINE[/red]")
        status_table.add_row("🔍 Slither:", "[green]READY[/green]" if tool_status.get("slither") else "[red]NOT FOUND[/red]")
        status_table.add_row("⚡ Mythril:", "[green]READY[/green]" if tool_status.get("mythril") else "[red]NOT FOUND[/red]")
        status_table.add_row("🛠️  Configuration:", "[green]LOADED[/green]")
        
        # Create main panel
        main_content = f"""[bold cyan]{banner_text}[/bold cyan]

[bold]🛡️  Comprehensive Smart Contract Security Auditing[/bold]

{status_table}

[dim]Type 'help' for available commands or 'audit <target>' to start an audit.[/dim]
        """
        
        panel = Panel(
            main_content,
            title="[bold green]Web3AuditMCP - Enhanced Security Analysis Platform[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    async def run_interactive_session(self):
        """Run the interactive client session."""
        
        self.display_banner()
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask(
                    "\n[bold cyan]web3audit[/bold cyan]",
                    default="help"
                ).strip()
                
                if not user_input:
                    continue
                
                # Add to history
                self.command_history.append(user_input)
                
                # Parse and execute command
                await self.execute_command(user_input)
                
            except KeyboardInterrupt:
                if Confirm.ask("\n[yellow]Exit Web3AuditMCP?[/yellow]"):
                    break
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
        
        self.console.print("\n[bold green]Thank you for using Web3AuditMCP! 🛡️[/bold green]")
    
    async def execute_command(self, command: str):
        """Execute a user command."""
        
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Command routing
        if cmd in ['help', 'h']:
            self.show_help()
        elif cmd in ['audit', 'a']:
            await self.run_audit_command(args)
        elif cmd in ['quick', 'q']:
            await self.run_quick_scan_command(args)
        elif cmd in ['status', 's']:
            await self.show_status()
        elif cmd in ['config', 'c']:
            await self.manage_config(args)
        elif cmd in ['model', 'm']:
            await self.manage_model(args)
        elif cmd in ['history']:
            self.show_history()
        elif cmd in ['export', 'e']:
            await self.export_results(args)
        elif cmd in ['clear', 'cls']:
            self.console.clear()
            self.display_banner()
        elif cmd in ['exit', 'quit', 'q']:
            raise KeyboardInterrupt
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("[dim]Type 'help' for available commands.[/dim]")
    
    def show_help(self):
        """Display help information."""
        
        help_table = Table(title="🔧 Available Commands")
        help_table.add_column("Command", style="cyan", width=20)
        help_table.add_column("Description", style="white")
        help_table.add_column("Example", style="dim")
        
        commands = [
            ("audit <target>", "Run comprehensive security audit", "audit ./contracts/"),
            ("quick <target>", "Run quick vulnerability scan", "quick MyContract.sol"),
            ("status", "Show system and tool status", "status"),
            ("config [action]", "Manage configuration", "config show"),
            ("model [action]", "Manage AI models", "model list"),
            ("history", "Show command history", "history"),
            ("export [format]", "Export last audit results", "export json"),
            ("clear", "Clear screen and show banner", "clear"),
            ("help", "Show this help message", "help"),
            ("exit", "Exit Web3AuditMCP", "exit")
        ]
        
        for cmd, desc, example in commands:
            help_table.add_row(cmd, desc, example)
        
        self.console.print(help_table)
        
        # Additional help sections
        self.console.print("\n[bold]🎯 Quick Start:[/bold]")
        self.console.print("1. [cyan]audit ./my-contract/[/cyan] - Audit a directory")
        self.console.print("2. [cyan]quick Contract.sol[/cyan] - Quick scan a file")
        self.console.print("3. [cyan]status[/cyan] - Check tool availability")
        
        self.console.print("\n[bold]🔍 Supported Targets:[/bold]")
        self.console.print("• Solidity files (.sol)")
        self.console.print("• Project directories (Foundry, Hardhat, Truffle)")
        self.console.print("• Git repositories (https://github.com/...)")
    
    async def run_audit_command(self, args: List[str]):
        """Run a comprehensive audit."""
        
        if not args:
            target = Prompt.ask("Enter target (file/directory/repo)")
        else:
            target = " ".join(args)
        
        if not target:
            self.console.print("[red]No target specified[/red]")
            return
        
        # Validate target
        if not self._validate_target(target):
            return
        
        # Run audit
        config = {'target': target}
        
        self.console.print(f"\n[bold green]🚀 Starting comprehensive audit of: {target}[/bold green]")
        
        try:
            report_panel = await self.orchestration_layer.start_audit(config)
            self.console.print(report_panel)
            
            # Ask if user wants to export results
            if Confirm.ask("\n[cyan]Export results?[/cyan]", default=False):
                format_choice = Prompt.ask("Format", choices=["json", "markdown"], default="json")
                await self.export_results([format_choice])
                
        except Exception as e:
            self.console.print(f"[red]Audit failed: {e}[/red]")
    
    async def run_quick_scan_command(self, args: List[str]):
        """Run a quick security scan."""
        
        if not args:
            target = Prompt.ask("Enter target for quick scan")
        else:
            target = " ".join(args)
        
        if not target:
            self.console.print("[red]No target specified[/red]")
            return
        
        # Validate target
        if not self._validate_target(target):
            return
        
        self.console.print(f"\n[bold yellow]⚡ Running quick scan of: {target}[/bold yellow]")
        
        try:
            report_panel = await self.orchestration_layer.quick_scan(target)
            self.console.print(report_panel)
            
        except Exception as e:
            self.console.print(f"[red]Quick scan failed: {e}[/red]")
    
    def _validate_target(self, target: str) -> bool:
        """Validate the audit target."""
        
        # Check if it's a URL
        if target.startswith(('http://', 'https://')):
            return True
        
        # Check if it's a file or directory
        if os.path.exists(target):
            return True
        
        # Check if it looks like a relative path
        if '/' in target or '\\' in target:
            self.console.print(f"[yellow]Warning: Target path '{target}' does not exist[/yellow]")
            return Confirm.ask("Continue anyway?", default=False)
        
        self.console.print(f"[red]Target '{target}' not found[/red]")
        return False
    
    async def show_status(self):
        """Show system and tool status."""
        
        # Get tool status
        tool_status = await self.orchestration_layer.get_tool_status()
        
        # Create status table
        status_table = Table(title="🔧 System Status")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", justify="center")
        status_table.add_column("Details", style="dim")
        
        # System components
        status_table.add_row(
            "Multi-Agent System",
            "[green]✅ ACTIVE[/green]",
            "3 agents ready"
        )
        
        status_table.add_row(
            "LLM Integration", 
            "[green]✅ READY[/green]" if self.ollama else "[red]❌ OFFLINE[/red]",
            f"Model: {self.config.model.default_model}" if self.ollama else "Ollama not available"
        )
        
        # Analysis tools
        for tool, available in tool_status.items():
            status_table.add_row(
                tool.title(),
                "[green]✅ READY[/green]" if available else "[red]❌ NOT FOUND[/red]",
                "Available for analysis" if available else "Install required"
            )
        
        # Configuration
        status_table.add_row(
            "Configuration",
            "[green]✅ LOADED[/green]",
            f"Profile: {self.config.config_version}"
        )
        
        self.console.print(status_table)
        
        # Show recent analysis history
        history = self.orchestration_layer.get_analysis_history()
        if history:
            self.console.print(f"\n[bold]📊 Recent Analyses: {len(history)}[/bold]")
            for i, analysis in enumerate(history[-3:], 1):
                target = analysis.get('target', 'Unknown')
                findings = len(analysis.get('results', {}).get('findings', []))
                self.console.print(f"  {i}. {target} - {findings} findings")
    
    async def manage_config(self, args: List[str]):
        """Manage configuration settings."""
        
        if not args:
            action = Prompt.ask("Config action", choices=["show", "edit", "reset", "export", "import"], default="show")
        else:
            action = args[0].lower()
        
        if action == "show":
            self._show_config()
        elif action == "edit":
            await self._edit_config()
        elif action == "reset":
            if Confirm.ask("Reset configuration to defaults?"):
                self.config_manager.reset_config()
                self.config = self.config_manager.get_config()
        elif action == "export":
            path = Prompt.ask("Export path", default="web3audit_config.toml")
            self.config_manager.export_config(path)
        elif action == "import":
            path = Prompt.ask("Import path")
            if os.path.exists(path):
                self.config_manager.import_config(path)
                self.config = self.config_manager.get_config()
            else:
                self.console.print(f"[red]File not found: {path}[/red]")
    
    def _show_config(self):
        """Show current configuration."""
        
        config_table = Table(title="⚙️ Current Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")
        config_table.add_column("Description", style="dim")
        
        # Model settings
        config_table.add_row("Default Model", self.config.model.default_model, "Primary LLM model")
        config_table.add_row("Temperature", str(self.config.model.temperature), "LLM creativity (0-2)")
        config_table.add_row("Max Tokens", str(self.config.model.max_tokens), "Response length limit")
        
        # Tool settings
        config_table.add_row("Slither Enabled", str(self.config.tools.slither_enabled), "Static analysis")
        config_table.add_row("Mythril Enabled", str(self.config.tools.mythril_enabled), "Symbolic execution")
        config_table.add_row("Foundry Enabled", str(self.config.tools.foundry_enabled), "Fuzzing tests")
        
        # Audit settings
        config_table.add_row("Parallel Execution", str(self.config.audit.parallel_execution), "Run tools in parallel")
        config_table.add_row("Detailed Reports", str(self.config.audit.detailed_reports), "Include full details")
        
        self.console.print(config_table)
    
    async def _edit_config(self):
        """Interactive configuration editing."""
        
        self.console.print("[bold]🔧 Configuration Editor[/bold]")
        
        # Model configuration
        if Confirm.ask("Edit model settings?", default=False):
            new_model = Prompt.ask("Default model", default=self.config.model.default_model)
            new_temp = float(Prompt.ask("Temperature (0-2)", default=str(self.config.model.temperature)))
            new_tokens = int(Prompt.ask("Max tokens", default=str(self.config.model.max_tokens)))
            
            self.config_manager.update_model_config(
                default_model=new_model,
                temperature=new_temp,
                max_tokens=new_tokens
            )
        
        # Tool configuration
        if Confirm.ask("Edit tool settings?", default=False):
            slither_enabled = Confirm.ask("Enable Slither?", default=self.config.tools.slither_enabled)
            mythril_enabled = Confirm.ask("Enable Mythril?", default=self.config.tools.mythril_enabled)
            foundry_enabled = Confirm.ask("Enable Foundry?", default=self.config.tools.foundry_enabled)
            
            self.config_manager.update_tool_config(
                slither_enabled=slither_enabled,
                mythril_enabled=mythril_enabled,
                foundry_enabled=foundry_enabled
            )
        
        # Reload configuration
        self.config = self.config_manager.get_config()
        self.console.print("[green]✅ Configuration updated[/green]")
    
    async def manage_model(self, args: List[str]):
        """Manage AI models."""
        
        if not self.ollama:
            self.console.print("[red]Ollama not available[/red]")
            return
        
        if not args:
            action = Prompt.ask("Model action", choices=["list", "pull", "select"], default="list")
        else:
            action = args[0].lower()
        
        if action == "list":
            await self._list_models()
        elif action == "pull":
            model_name = Prompt.ask("Model name to pull")
            await self._pull_model(model_name)
        elif action == "select":
            await self._select_model()
    
    async def _list_models(self):
        """List available models."""
        
        try:
            models = self.ollama.list()
            model_list = models.get('models', [])
            
            if not model_list:
                self.console.print("[yellow]No models found[/yellow]")
                return
            
            model_table = Table(title="🤖 Available Models")
            model_table.add_column("Name", style="cyan")
            model_table.add_column("Size", justify="right")
            model_table.add_column("Modified", style="dim")
            model_table.add_column("Current", justify="center")
            
            for model in model_list:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0)
                modified = model.get('modified_at', 'Unknown')
                is_current = "✅" if name == self.config.model.default_model else ""
                
                # Format size
                size_str = f"{size // (1024**3):.1f}GB" if size > 1024**3 else f"{size // (1024**2)}MB"
                
                model_table.add_row(name, size_str, modified[:10], is_current)
            
            self.console.print(model_table)
            
        except Exception as e:
            self.console.print(f"[red]Failed to list models: {e}[/red]")
    
    async def _pull_model(self, model_name: str):
        """Pull a model from Ollama."""
        
        self.console.print(f"[yellow]Pulling model: {model_name}[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task(f"Downloading {model_name}...", total=None)
            
            try:
                # This is a simplified version - real implementation would show progress
                self.ollama.pull(model_name)
                progress.update(task, description=f"✅ {model_name} downloaded")
                self.console.print(f"[green]Model {model_name} ready[/green]")
                
            except Exception as e:
                self.console.print(f"[red]Failed to pull model: {e}[/red]")
    
    async def _select_model(self):
        """Select default model."""
        
        try:
            models = self.ollama.list()
            model_names = [model['name'] for model in models.get('models', [])]
            
            if not model_names:
                self.console.print("[yellow]No models available[/yellow]")
                return
            
            # Show current model
            self.console.print(f"Current model: [cyan]{self.config.model.default_model}[/cyan]")
            
            # Let user select
            for i, name in enumerate(model_names, 1):
                self.console.print(f"  {i}. {name}")
            
            choice = Prompt.ask("Select model number", default="1")
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(model_names):
                    selected_model = model_names[index]
                    self.config_manager.update_model_config(default_model=selected_model)
                    self.config = self.config_manager.get_config()
                    self.console.print(f"[green]✅ Default model set to: {selected_model}[/green]")
                else:
                    self.console.print("[red]Invalid selection[/red]")
            except ValueError:
                self.console.print("[red]Invalid input[/red]")
                
        except Exception as e:
            self.console.print(f"[red]Failed to select model: {e}[/red]")
    
    def show_history(self):
        """Show command history."""
        
        if not self.command_history:
            self.console.print("[dim]No command history[/dim]")
            return
        
        history_table = Table(title="📜 Command History")
        history_table.add_column("#", width=4)
        history_table.add_column("Command", style="cyan")
        
        for i, cmd in enumerate(self.command_history[-10:], 1):
            history_table.add_row(str(i), cmd)
        
        self.console.print(history_table)
    
    async def export_results(self, args: List[str]):
        """Export audit results."""
        
        if not args:
            format_choice = Prompt.ask("Export format", choices=["json", "markdown"], default="json")
        else:
            format_choice = args[0].lower()
        
        try:
            results = self.orchestration_layer.export_results(format_choice)
            
            if results == "No analysis results available":
                self.console.print("[yellow]No audit results to export[/yellow]")
                return
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"web3audit_results_{timestamp}.{format_choice}"
            
            # Write to file
            with open(filename, 'w') as f:
                f.write(results)
            
            self.console.print(f"[green]✅ Results exported to: {filename}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]Export failed: {e}[/red]")

def run_client():
    """Entry point for the Web3AuditMCP client."""
    client = Web3AuditClient()
    asyncio.run(client.run_interactive_session())

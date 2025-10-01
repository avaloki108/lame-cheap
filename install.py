#!/usr/bin/env python3
"""Enhanced installation script for Web3AuditMCP with comprehensive setup."""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Confirm

console = Console()

class Web3AuditInstaller:
    """Comprehensive installer for Web3AuditMCP and its dependencies."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.requirements_met = True
        
    def check_requirements(self):
        """Check system requirements."""
        
        console.print("[bold]🔍 Checking System Requirements[/bold]")
        
        req_table = Table(title="System Requirements")
        req_table.add_column("Requirement", style="cyan")
        req_table.add_column("Status", justify="center")
        req_table.add_column("Details", style="dim")
        
        # Python version check
        if self.python_version >= (3, 8):
            req_table.add_row("Python 3.8+", "[green]✅ PASS[/green]", f"Found {sys.version}")
        else:
            req_table.add_row("Python 3.8+", "[red]❌ FAIL[/red]", f"Found {sys.version}")
            self.requirements_met = False
        
        # Node.js check
        node_version = self._check_command("node --version")
        if node_version:
            req_table.add_row("Node.js", "[green]✅ PASS[/green]", node_version.strip())
        else:
            req_table.add_row("Node.js", "[yellow]⚠️ MISSING[/yellow]", "Required for some tools")
        
        # Docker check
        docker_version = self._check_command("docker --version")
        if docker_version:
            req_table.add_row("Docker", "[green]✅ PASS[/green]", docker_version.strip())
        else:
            req_table.add_row("Docker", "[yellow]⚠️ MISSING[/yellow]", "Optional for containerized analysis")
        
        # Git check
        git_version = self._check_command("git --version")
        if git_version:
            req_table.add_row("Git", "[green]✅ PASS[/green]", git_version.strip())
        else:
            req_table.add_row("Git", "[red]❌ MISSING[/red]", "Required for repository analysis")
            self.requirements_met = False
        
        console.print(req_table)
        
        if not self.requirements_met:
            console.print("\n[red]❌ Some requirements are not met. Please install missing dependencies.[/red]")
            return False
        
        console.print("\n[green]✅ All requirements satisfied![/green]")
        return True
    
    def _check_command(self, command):
        """Check if a command exists and return its output."""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
    
    def install_python_dependencies(self):
        """Install Python dependencies using uv or pip."""
        
        console.print("\n[bold]📦 Installing Python Dependencies[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Check if uv is available
            task = progress.add_task("Checking package managers...", total=None)
            
            uv_available = self._check_command("uv --version")
            
            if uv_available:
                progress.update(task, description="Installing with uv (fast)...")
                install_cmd = ["uv", "pip", "install", "-e", "."]
            else:
                progress.update(task, description="Installing with pip...")
                install_cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
            
            try:
                result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent
                )
                
                if result.returncode == 0:
                    progress.update(task, description="✅ Python dependencies installed")
                    console.print("[green]✅ Python dependencies installed successfully[/green]")
                else:
                    console.print(f"[red]❌ Installation failed: {result.stderr}[/red]")
                    return False
                    
            except Exception as e:
                console.print(f"[red]❌ Installation error: {e}[/red]")
                return False
        
        return True
    
    def install_security_tools(self):
        """Install security analysis tools."""
        
        console.print("\n[bold]🛠️ Installing Security Analysis Tools[/bold]")
        
        tools_to_install = []
        
        # Check which tools need installation
        if not self._check_command("slither --version"):
            tools_to_install.append(("Slither", "pip install slither-analyzer"))
        
        if not self._check_command("myth --version"):
            tools_to_install.append(("Mythril", "pip install mythril"))
        
        if not self._check_command("forge --version"):
            tools_to_install.append(("Foundry", self._get_foundry_install_cmd()))
        
        if not tools_to_install:
            console.print("[green]✅ All security tools already installed[/green]")
            return True
        
        # Install missing tools
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for tool_name, install_cmd in tools_to_install:
                task = progress.add_task(f"Installing {tool_name}...", total=None)
                
                try:
                    if tool_name == "Foundry":
                        # Special handling for Foundry
                        success = self._install_foundry()
                    else:
                        result = subprocess.run(
                            install_cmd.split(),
                            capture_output=True,
                            text=True,
                            timeout=300  # 5 minutes timeout
                        )
                        success = result.returncode == 0
                    
                    if success:
                        progress.update(task, description=f"✅ {tool_name} installed")
                    else:
                        progress.update(task, description=f"❌ {tool_name} failed")
                        console.print(f"[yellow]⚠️ {tool_name} installation failed. You can install it manually later.[/yellow]")
                        
                except Exception as e:
                    console.print(f"[yellow]⚠️ {tool_name} installation error: {e}[/yellow]")
        
        return True
    
    def _get_foundry_install_cmd(self):
        """Get the appropriate Foundry installation command."""
        if self.system == "linux" or self.system == "darwin":
            return "curl -L https://foundry.paradigm.xyz | bash"
        else:
            return "# Manual installation required for Windows"
    
    def _install_foundry(self):
        """Install Foundry using the official installer."""
        try:
            if self.system == "windows":
                console.print("[yellow]⚠️ Foundry installation on Windows requires manual setup[/yellow]")
                console.print("Please visit: https://book.getfoundry.sh/getting-started/installation")
                return False
            
            # Download and run Foundry installer
            install_script = subprocess.run([
                "curl", "-L", "https://foundry.paradigm.xyz"
            ], capture_output=True, text=True, timeout=60)
            
            if install_script.returncode == 0:
                # Run the installer
                result = subprocess.run([
                    "bash", "-c", install_script.stdout
                ], capture_output=True, text=True, timeout=300)
                
                return result.returncode == 0
            
            return False
            
        except Exception:
            return False
    
    def setup_ollama(self):
        """Setup Ollama for LLM integration."""
        
        console.print("\n[bold]🧠 Setting up Ollama (LLM Integration)[/bold]")
        
        # Check if Ollama is already installed
        if self._check_command("ollama --version"):
            console.print("[green]✅ Ollama already installed[/green]")
            
            if Confirm.ask("Download recommended models?", default=True):
                self._download_recommended_models()
            
            return True
        
        # Install Ollama
        console.print("Installing Ollama...")
        
        try:
            if self.system == "linux" or self.system == "darwin":
                install_cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
                result = subprocess.run(
                    ["bash", "-c", install_cmd],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    console.print("[green]✅ Ollama installed successfully[/green]")
                    
                    # Start Ollama service
                    subprocess.run(["ollama", "serve"], timeout=5)
                    
                    if Confirm.ask("Download recommended models?", default=True):
                        self._download_recommended_models()
                    
                    return True
                else:
                    console.print(f"[red]❌ Ollama installation failed: {result.stderr}[/red]")
                    return False
            else:
                console.print("[yellow]⚠️ Please install Ollama manually on Windows[/yellow]")
                console.print("Visit: https://ollama.ai/download")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Ollama installation error: {e}[/red]")
            return False
    
    def _download_recommended_models(self):
        """Download recommended AI models."""
        
        recommended_models = [
            "qwen2.5-coder:7b",  # Good for code analysis
            "llama3.1:8b",       # General purpose
            "codellama:7b"       # Code-specific
        ]
        
        console.print("\n[bold]📥 Downloading Recommended Models[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for model in recommended_models:
                task = progress.add_task(f"Downloading {model}...", total=None)
                
                try:
                    result = subprocess.run(
                        ["ollama", "pull", model],
                        capture_output=True,
                        text=True,
                        timeout=600  # 10 minutes per model
                    )
                    
                    if result.returncode == 0:
                        progress.update(task, description=f"✅ {model} downloaded")
                    else:
                        progress.update(task, description=f"❌ {model} failed")
                        
                except Exception as e:
                    console.print(f"[yellow]⚠️ Model {model} download failed: {e}[/yellow]")
    
    def create_config(self):
        """Create initial configuration."""
        
        console.print("\n[bold]⚙️ Creating Configuration[/bold]")
        
        config_dir = Path.home() / ".web3audit"
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "config.toml"
        
        if config_file.exists():
            if not Confirm.ask("Configuration exists. Overwrite?", default=False):
                return True
        
        # Create default configuration
        default_config = '''[config]
version = "1.0.0"

[model]
default_model = "qwen2.5-coder:7b"
temperature = 0.7
top_p = 0.9
max_tokens = 2000

[tools]
slither_enabled = true
mythril_enabled = true
foundry_enabled = true

[audit]
parallel_execution = true
detailed_reports = true
export_format = "json"

[output]
console_style = "rich"
log_level = "INFO"
'''
        
        try:
            with open(config_file, 'w') as f:
                f.write(default_config)
            
            console.print(f"[green]✅ Configuration created at: {config_file}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Configuration creation failed: {e}[/red]")
            return False
    
    def run_installation(self):
        """Run the complete installation process."""
        
        # Display banner
        banner = """
╦ ╦┌─┐┌┐ ╔═╗╔═╗┬ ┬┌┬┐┬┌┬┐╔╦╗╔═╗╔═╗
║║║├┤ ├┴┐╠═╣║ ║ ║ │││ │ ║║║║ ║╠═╝
╚╩╝└─┘└─┘╩ ╩╚═╝ ╚═╝─┴┘┴ ┴ ╩ ╩╚═╝╩  

Enhanced Smart Contract Security Auditing Platform
        """
        
        console.print(Panel(
            f"[bold cyan]{banner}[/bold cyan]\n\n[bold]🚀 Installation Wizard[/bold]",
            title="Web3AuditMCP Installer",
            border_style="green"
        ))
        
        # Step 1: Check requirements
        if not self.check_requirements():
            return False
        
        # Step 2: Install Python dependencies
        if not self.install_python_dependencies():
            return False
        
        # Step 3: Install security tools
        if Confirm.ask("\nInstall security analysis tools (Slither, Mythril, Foundry)?", default=True):
            self.install_security_tools()
        
        # Step 4: Setup Ollama
        if Confirm.ask("\nSetup Ollama for AI-enhanced analysis?", default=True):
            self.setup_ollama()
        
        # Step 5: Create configuration
        self.create_config()
        
        # Installation complete
        console.print("\n" + "="*60)
        console.print(Panel(
            "[bold green]🎉 Installation Complete![/bold green]\n\n"
            "[bold]Next Steps:[/bold]\n"
            "1. Run: [cyan]web3audit-mcp[/cyan] to start the client\n"
            "2. Try: [cyan]web3audit-mcp audit ./my-contract/[/cyan]\n"
            "3. Check status: [cyan]web3audit-mcp status[/cyan]\n\n"
            "[dim]For help: web3audit-mcp --help[/dim]",
            title="🛡️ Web3AuditMCP Ready",
            border_style="green"
        ))
        
        return True

def main():
    """Main installation entry point."""
    installer = Web3AuditInstaller()
    
    try:
        success = installer.run_installation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Installation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Installation failed: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()

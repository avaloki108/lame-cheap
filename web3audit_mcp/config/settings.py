"""Configuration settings for Web3AuditMCP."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import toml
from dataclasses import dataclass, asdict
from rich.console import Console

@dataclass
class ModelConfig:
    """Configuration for AI model settings."""
    default_model: str = "qwen3-coder:30b"
    fallback_model: str = "gpt-oss:20b"
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 4096
    system_prompt: str = """You are a smart contract security expert. Analyze code for vulnerabilities, 
    provide specific recommendations, and reference common attack patterns."""

@dataclass
class ToolConfig:
    """Configuration for security analysis tools."""
    slither_enabled: bool = True
    mythril_enabled: bool = True
    foundry_enabled: bool = True
    custom_checks_enabled: bool = True
    
    # Tool-specific settings
    slither_detectors: List[str] = None
    mythril_timeout: int = 300
    foundry_fuzz_runs: int = 1000
    
    # Installation settings
    auto_install: bool = True
    install_timeout: int = 600

@dataclass
class AuditConfig:
    """Configuration for audit execution."""
    parallel_execution: bool = True
    max_concurrent_tools: int = 3
    timeout_per_tool: int = 600
    
    # Report settings
    detailed_reports: bool = True
    include_remediation: bool = True
    export_formats: List[str] = None  # ['json', 'markdown', 'pdf']
    
    # Risk scoring
    high_severity_weight: int = 10
    medium_severity_weight: int = 5
    low_severity_weight: int = 1

@dataclass
class UIConfig:
    """Configuration for user interface."""
    theme: str = "dark"
    show_progress: bool = True
    auto_clear: bool = False
    max_history: int = 100
    
    # Console settings
    width: Optional[int] = None
    height: Optional[int] = None
    color_system: str = "auto"

@dataclass
class Web3AuditConfig:
    """Main configuration class for Web3AuditMCP."""
    model: ModelConfig
    tools: ToolConfig
    audit: AuditConfig
    ui: UIConfig
    
    # Global settings
    debug: bool = False
    log_level: str = "INFO"
    config_version: str = "1.0"

class ConfigManager:
    """Manages configuration loading, saving, and validation."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.config_dir = Path.home() / ".web3audit-mcp"
        self.config_file = self.config_dir / "config.toml"
        self.config: Optional[Web3AuditConfig] = None
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
    
    def load_config(self) -> Web3AuditConfig:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = toml.load(f)
                
                # Parse configuration sections
                model_config = ModelConfig(**config_data.get('model', {}))
                tools_config = ToolConfig(**config_data.get('tools', {}))
                audit_config = AuditConfig(**config_data.get('audit', {}))
                ui_config = UIConfig(**config_data.get('ui', {}))
                
                # Handle global settings
                global_settings = {k: v for k, v in config_data.items() 
                                 if k not in ['model', 'tools', 'audit', 'ui']}
                
                self.config = Web3AuditConfig(
                    model=model_config,
                    tools=tools_config,
                    audit=audit_config,
                    ui=ui_config,
                    **global_settings
                )
                
                self.console.print("[green]✅ Configuration loaded successfully[/green]")
                
            except Exception as e:
                self.console.print(f"[red]❌ Error loading config: {e}[/red]")
                self.console.print("[yellow]Using default configuration[/yellow]")
                self.config = self._create_default_config()
        else:
            self.console.print("[yellow]No config file found, creating default[/yellow]")
            self.config = self._create_default_config()
            self.save_config()
        
        return self.config
    
    def _create_default_config(self) -> Web3AuditConfig:
        """Create default configuration."""
        return Web3AuditConfig(
            model=ModelConfig(),
            tools=ToolConfig(
                slither_detectors=[],
                export_formats=['json', 'markdown']
            ),
            audit=AuditConfig(
                export_formats=['json', 'markdown']
            ),
            ui=UIConfig()
        )
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        if not self.config:
            return False
        
        try:
            config_dict = {
                'model': asdict(self.config.model),
                'tools': asdict(self.config.tools),
                'audit': asdict(self.config.audit),
                'ui': asdict(self.config.ui),
                'debug': self.config.debug,
                'log_level': self.config.log_level,
                'config_version': self.config.config_version
            }
            
            with open(self.config_file, 'w') as f:
                toml.dump(config_dict, f)
            
            self.console.print(f"[green]✅ Configuration saved to {self.config_file}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Error saving config: {e}[/red]")
            return False
    
    def get_config(self) -> Web3AuditConfig:
        """Get current configuration, loading if necessary."""
        if not self.config:
            self.load_config()
        return self.config
    
    def update_model_config(self, **kwargs) -> bool:
        """Update model configuration."""
        if not self.config:
            self.load_config()
        
        for key, value in kwargs.items():
            if hasattr(self.config.model, key):
                setattr(self.config.model, key, value)
            else:
                self.console.print(f"[red]Unknown model config key: {key}[/red]")
                return False
        
        return self.save_config()
    
    def update_tool_config(self, **kwargs) -> bool:
        """Update tool configuration."""
        if not self.config:
            self.load_config()
        
        for key, value in kwargs.items():
            if hasattr(self.config.tools, key):
                setattr(self.config.tools, key, value)
            else:
                self.console.print(f"[red]Unknown tool config key: {key}[/red]")
                return False
        
        return self.save_config()
    
    def update_audit_config(self, **kwargs) -> bool:
        """Update audit configuration."""
        if not self.config:
            self.load_config()
        
        for key, value in kwargs.items():
            if hasattr(self.config.audit, key):
                setattr(self.config.audit, key, value)
            else:
                self.console.print(f"[red]Unknown audit config key: {key}[/red]")
                return False
        
        return self.save_config()
    
    def reset_config(self) -> bool:
        """Reset configuration to defaults."""
        self.config = self._create_default_config()
        return self.save_config()
    
    def export_config(self, output_path: str) -> bool:
        """Export configuration to specified path."""
        if not self.config:
            self.load_config()
        
        try:
            config_dict = {
                'model': asdict(self.config.model),
                'tools': asdict(self.config.tools),
                'audit': asdict(self.config.audit),
                'ui': asdict(self.config.ui),
                'debug': self.config.debug,
                'log_level': self.config.log_level,
                'config_version': self.config.config_version
            }
            
            with open(output_path, 'w') as f:
                toml.dump(config_dict, f)
            
            self.console.print(f"[green]✅ Configuration exported to {output_path}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Error exporting config: {e}[/red]")
            return False
    
    def import_config(self, input_path: str) -> bool:
        """Import configuration from specified path."""
        try:
            with open(input_path, 'r') as f:
                config_data = toml.load(f)
            
            # Validate and load configuration
            model_config = ModelConfig(**config_data.get('model', {}))
            tools_config = ToolConfig(**config_data.get('tools', {}))
            audit_config = AuditConfig(**config_data.get('audit', {}))
            ui_config = UIConfig(**config_data.get('ui', {}))
            
            global_settings = {k: v for k, v in config_data.items() 
                             if k not in ['model', 'tools', 'audit', 'ui']}
            
            self.config = Web3AuditConfig(
                model=model_config,
                tools=tools_config,
                audit=audit_config,
                ui=ui_config,
                **global_settings
            )
            
            # Save imported configuration
            success = self.save_config()
            if success:
                self.console.print(f"[green]✅ Configuration imported from {input_path}[/green]")
            
            return success
            
        except Exception as e:
            self.console.print(f"[red]❌ Error importing config: {e}[/red]")
            return False
    
    def validate_config(self) -> List[str]:
        """Validate current configuration and return any issues."""
        issues = []
        
        if not self.config:
            issues.append("No configuration loaded")
            return issues
        
        # Validate model config
        if self.config.model.temperature < 0 or self.config.model.temperature > 2:
            issues.append("Model temperature should be between 0 and 2")
        
        if self.config.model.top_p < 0 or self.config.model.top_p > 1:
            issues.append("Model top_p should be between 0 and 1")
        
        if self.config.model.max_tokens < 1:
            issues.append("Model max_tokens should be positive")
        
        # Validate tool config
        if self.config.tools.mythril_timeout < 60:
            issues.append("Mythril timeout should be at least 60 seconds")
        
        if self.config.tools.foundry_fuzz_runs < 1:
            issues.append("Foundry fuzz runs should be positive")
        
        # Validate audit config
        if self.config.audit.max_concurrent_tools < 1:
            issues.append("Max concurrent tools should be positive")
        
        if self.config.audit.timeout_per_tool < 60:
            issues.append("Tool timeout should be at least 60 seconds")
        
        return issues
    
    def get_ollama_options(self) -> Dict[str, Any]:
        """Get Ollama-compatible options from model config."""
        if not self.config:
            self.load_config()
        
        return {
            'temperature': self.config.model.temperature,
            'top_p': self.config.model.top_p,
            'num_predict': self.config.model.max_tokens
        }
    
    def get_tool_settings(self, tool_name: str) -> Dict[str, Any]:
        """Get settings for a specific tool."""
        if not self.config:
            self.load_config()
        
        settings = {}
        
        if tool_name == 'slither':
            settings = {
                'enabled': self.config.tools.slither_enabled,
                'detectors': self.config.tools.slither_detectors or [],
                'timeout': self.config.audit.timeout_per_tool
            }
        elif tool_name == 'mythril':
            settings = {
                'enabled': self.config.tools.mythril_enabled,
                'timeout': self.config.tools.mythril_timeout
            }
        elif tool_name == 'foundry':
            settings = {
                'enabled': self.config.tools.foundry_enabled,
                'fuzz_runs': self.config.tools.foundry_fuzz_runs,
                'timeout': self.config.audit.timeout_per_tool
            }
        
        return settings

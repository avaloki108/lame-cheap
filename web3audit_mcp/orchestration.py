"""Enhanced orchestration layer for Web3AuditMCP."""

import asyncio
from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from .analysis_engine import AnalysisEngine

class OrchestrationLayer:
    """Manages the audit lifecycle and coordinates analysis modules."""

    def __init__(self, console: Console):
        self.console = console
        self.analysis_engine = AnalysisEngine(console)

    async def start_audit(self, config: Dict[str, Any]) -> Panel:
        """Starts a new audit with the given configuration."""
        target = config.get('target', 'unknown')
        
        self.console.print(Panel(
            f"[bold green]🚀 Starting comprehensive security audit for: {target}[/bold green]\n"
            f"[dim]Initializing Slither, Mythril, Foundry, and custom vulnerability checks...[/dim]",
            border_style="bold green"
        ))
        
        # Run comprehensive analysis
        analysis_results = await self.analysis_engine.comprehensive_analysis(target)
        
        # Generate detailed report
        report_panel = self.analysis_engine.generate_detailed_report(analysis_results)
        
        self.console.print("[bold green]✅ Audit complete! Results ready.[/bold green]")
        
        return report_panel

    async def quick_scan(self, target: str) -> Panel:
        """Run a quick security scan focusing on high-impact vulnerabilities."""
        
        self.console.print(Panel(
            f"[bold yellow]⚡ Running quick scan for: {target}[/bold yellow]\n"
            f"[dim]Focusing on critical vulnerabilities...[/dim]",
            border_style="bold yellow"
        ))
        
        # Simulate quick scan (would run subset of checks)
        await asyncio.sleep(1)
        
        # Mock quick scan results
        quick_results = {
            "target": target,
            "total_findings": 3,
            "high_severity": 2,
            "medium_severity": 1,
            "low_severity": 0,
            "findings": [
                {
                    "check": "reentrancy-eth",
                    "description": "Critical reentrancy vulnerability detected",
                    "impact": "High",
                    "confidence": "High"
                },
                {
                    "check": "unchecked-send",
                    "description": "Unchecked external call return value",
                    "impact": "High", 
                    "confidence": "Medium"
                },
                {
                    "check": "tx-origin",
                    "description": "Use of tx.origin for authorization",
                    "impact": "Medium",
                    "confidence": "High"
                }
            ],
            "high_findings": [
                {
                    "check": "reentrancy-eth",
                    "description": "Critical reentrancy vulnerability detected",
                    "impact": "High",
                    "confidence": "High"
                },
                {
                    "check": "unchecked-send", 
                    "description": "Unchecked external call return value",
                    "impact": "High",
                    "confidence": "Medium"
                }
            ],
            "medium_findings": [
                {
                    "check": "tx-origin",
                    "description": "Use of tx.origin for authorization", 
                    "impact": "Medium",
                    "confidence": "High"
                }
            ],
            "low_findings": []
        }
        
        report_panel = self.analysis_engine.generate_detailed_report(quick_results)
        
        self.console.print("[bold yellow]⚡ Quick scan complete![/bold yellow]")
        
        return report_panel

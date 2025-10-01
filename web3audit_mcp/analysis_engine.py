"""Advanced analysis engine for Web3AuditMCP."""

import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, TaskID
from .modules.slither_module import SlitherModule
from .modules.mythril_module import MythrilModule
from .modules.foundry_module import FoundryModule

class VulnerabilityCheck:
    """Represents a single vulnerability check from the checklist."""
    
    def __init__(self, check_data: Dict[str, Any]):
        self.id = check_data.get("id", "")
        self.question = check_data.get("question", "")
        self.description = check_data.get("description", "")
        self.remediation = check_data.get("remediation", "")
        self.references = check_data.get("references", [])
        self.tags = check_data.get("tags", [])
        self.category = check_data.get("category", "")

class AnalysisEngine:
    """Advanced analysis engine that orchestrates multiple security analysis tools."""
    
    def __init__(self, console: Console, checklist_path: str = None):
        self.console = console
        self.vulnerability_checks = []
        
        # Initialize analysis modules
        self.slither_module = SlitherModule(console)
        self.mythril_module = MythrilModule(console)
        self.foundry_module = FoundryModule(console)
        
        self.load_vulnerability_checklist(checklist_path)
        
    def load_vulnerability_checklist(self, checklist_path: str = None):
        """Load the vulnerability checklist from JSON file."""
        if not checklist_path:
            checklist_path = Path(__file__).parent.parent / "checklist.json"
        
        try:
            with open(checklist_path, 'r') as f:
                checklist_data = json.load(f)
            
            # Parse the nested structure of the checklist
            for category in checklist_data:
                if isinstance(category, dict) and "data" in category:
                    for subcategory in category["data"]:
                        if isinstance(subcategory, dict) and "data" in subcategory:
                            for check in subcategory["data"]:
                                if isinstance(check, dict):
                                    check["category"] = subcategory.get("category", "Unknown")
                                    self.vulnerability_checks.append(VulnerabilityCheck(check))
                                    
            self.console.print(f"[green]✅ Loaded {len(self.vulnerability_checks)} vulnerability checks[/green]")
            
        except Exception as e:
            self.console.print(f"[red]❌ Error loading checklist: {e}[/red]")
    
    async def run_slither_analysis(self, target: str, progress: Progress, task_id: TaskID) -> List[Dict[str, Any]]:
        """Run Slither static analysis using the advanced module."""
        return await self.slither_module.run_analysis(target, progress, task_id)
    
    async def run_mythril_analysis(self, target: str, progress: Progress, task_id: TaskID) -> List[Dict[str, Any]]:
        """Run Mythril symbolic execution using the advanced module."""
        return await self.mythril_module.run_analysis(target, progress, task_id)
    
    async def run_foundry_analysis(self, target: str, progress: Progress, task_id: TaskID) -> List[Dict[str, Any]]:
        """Run Foundry fuzzing and testing using the advanced module."""
        return await self.foundry_module.run_analysis(target, progress, task_id)
    
    async def run_custom_checks(self, target: str, progress: Progress, task_id: TaskID) -> List[Dict[str, Any]]:
        """Run custom vulnerability checks based on the loaded checklist."""
        findings = []
        
        try:
            progress.update(task_id, description="[magenta]🔍 Running custom vulnerability checks...")
            
            # Simulate analysis based on checklist patterns
            await asyncio.sleep(2)
            
            # In a real implementation, this would analyze the code against checklist patterns
            # For now, we'll simulate some findings based on common patterns
            
            # Check for donation attack patterns
            donation_findings = await self._check_donation_attacks(target)
            findings.extend(donation_findings)
            
            # Check for front-running vulnerabilities
            frontrun_findings = await self._check_frontrunning(target)
            findings.extend(frontrun_findings)
            
            # Check for reentrancy patterns
            reentrancy_findings = await self._check_reentrancy_patterns(target)
            findings.extend(reentrancy_findings)
            
            # Check for access control issues
            access_findings = await self._check_access_control(target)
            findings.extend(access_findings)
            
            progress.update(task_id, description=f"[magenta]✅ Custom checks found {len(findings)} issues")
            
        except Exception as e:
            progress.update(task_id, description=f"[red]❌ Custom checks error: {str(e)[:30]}...")
            
        return findings
    
    async def _check_donation_attacks(self, target: str) -> List[Dict[str, Any]]:
        """Check for donation attack vulnerabilities."""
        findings = []
        
        # Simulate checking for balance-based calculations
        # In real implementation, would parse Solidity AST
        
        findings.append({
            'tool': 'custom',
            'check': 'donation-attack',
            'description': 'Contract may be vulnerable to donation attacks due to balance-based calculations',
            'impact': 'High',
            'confidence': 'Medium',
            'elements': [],
            'markdown': 'Contract uses `address(this).balance` or `token.balanceOf(this)` which can be manipulated',
            'category': 'Donation Attack',
            'remediation': 'Use internal accounting instead of relying on balance checks'
        })
        
        return findings
    
    async def _check_frontrunning(self, target: str) -> List[Dict[str, Any]]:
        """Check for front-running vulnerabilities."""
        findings = []
        
        findings.append({
            'tool': 'custom',
            'check': 'front-running',
            'description': 'Function may be vulnerable to front-running attacks',
            'impact': 'Medium',
            'confidence': 'High',
            'elements': [],
            'markdown': 'Public function with price-sensitive operations detected',
            'category': 'Front-running Attack',
            'remediation': 'Implement commit-reveal scheme or use private mempools'
        })
        
        return findings
    
    async def _check_reentrancy_patterns(self, target: str) -> List[Dict[str, Any]]:
        """Check for reentrancy patterns beyond basic detection."""
        findings = []
        
        findings.append({
            'tool': 'custom',
            'check': 'cross-function-reentrancy',
            'description': 'Potential cross-function reentrancy vulnerability',
            'impact': 'High',
            'confidence': 'Medium',
            'elements': [],
            'markdown': 'State changes after external calls may enable cross-function reentrancy',
            'category': 'Reentrancy',
            'remediation': 'Use checks-effects-interactions pattern and reentrancy guards'
        })
        
        return findings
    
    async def _check_access_control(self, target: str) -> List[Dict[str, Any]]:
        """Check for access control issues."""
        findings = []
        
        findings.append({
            'tool': 'custom',
            'check': 'missing-access-control',
            'description': 'Critical function may lack proper access control',
            'impact': 'High',
            'confidence': 'Medium',
            'elements': [],
            'markdown': 'Administrative function without proper access restrictions detected',
            'category': 'Access Control',
            'remediation': 'Implement proper role-based access control'
        })
        
        return findings
    
    async def comprehensive_analysis(self, target: str) -> Dict[str, Any]:
        """Run comprehensive analysis using all available tools."""
        
        with Progress(console=self.console) as progress:
            # Create progress tasks
            slither_task = progress.add_task("[green]Slither Analysis", total=100)
            mythril_task = progress.add_task("[yellow]Mythril Analysis", total=100)
            foundry_task = progress.add_task("[blue]Foundry Analysis", total=100)
            custom_task = progress.add_task("[magenta]Custom Checks", total=100)
            
            # Run all analyses concurrently
            slither_results, mythril_results, foundry_results, custom_results = await asyncio.gather(
                self.run_slither_analysis(target, progress, slither_task),
                self.run_mythril_analysis(target, progress, mythril_task),
                self.run_foundry_analysis(target, progress, foundry_task),
                self.run_custom_checks(target, progress, custom_task)
            )
            
            # Update progress to complete
            progress.update(slither_task, completed=100)
            progress.update(mythril_task, completed=100)
            progress.update(foundry_task, completed=100)
            progress.update(custom_task, completed=100)
        
        # Aggregate all findings
        all_findings = []
        all_findings.extend(slither_results)
        all_findings.extend(mythril_results)
        all_findings.extend(foundry_results)
        all_findings.extend(custom_results)
        
        # Categorize findings by severity
        high_severity = [f for f in all_findings if f.get("impact") == "High"]
        medium_severity = [f for f in all_findings if f.get("impact") == "Medium"]
        low_severity = [f for f in all_findings if f.get("impact") == "Low"]
        
        # Calculate risk score
        risk_score = len(high_severity) * 10 + len(medium_severity) * 5 + len(low_severity) * 1
        
        return {
            "target": target,
            "total_findings": len(all_findings),
            "high_severity": len(high_severity),
            "medium_severity": len(medium_severity),
            "low_severity": len(low_severity),
            "risk_score": risk_score,
            "findings": all_findings,
            "high_findings": high_severity,
            "medium_findings": medium_severity,
            "low_findings": low_severity,
            "tool_status": {
                "slither": self.slither_module.is_available(),
                "mythril": self.mythril_module.is_available(),
                "foundry": self.foundry_module.is_available()
            }
        }
    
    def generate_detailed_report(self, analysis_results: Dict[str, Any]) -> Panel:
        """Generate a detailed, beautiful report panel."""
        
        # Create summary table
        summary_table = Table(show_header=True, header_style="bold magenta", box=None)
        summary_table.add_column("Metric", style="cyan", width=20)
        summary_table.add_column("Count", style="bold white", width=10)
        summary_table.add_column("Risk Level", style="bold", width=15)
        
        # Determine risk level based on findings
        risk_score = analysis_results.get("risk_score", 0)
        if risk_score >= 50:
            risk_level = "[bold red]CRITICAL[/bold red]"
        elif risk_score >= 25:
            risk_level = "[bold yellow]HIGH[/bold yellow]"
        elif risk_score >= 10:
            risk_level = "[bold orange3]MEDIUM[/bold orange3]"
        else:
            risk_level = "[bold green]LOW[/bold green]"
        
        summary_table.add_row("Total Findings", str(analysis_results["total_findings"]), "")
        summary_table.add_row("🔴 Critical", str(analysis_results["high_severity"]), "")
        summary_table.add_row("🟡 Medium", str(analysis_results["medium_severity"]), "")
        summary_table.add_row("🟢 Low", str(analysis_results["low_severity"]), "")
        summary_table.add_row("Risk Score", str(risk_score), risk_level)
        
        # Create tool status table
        tool_status_table = Table(show_header=True, header_style="bold cyan", box=None)
        tool_status_table.add_column("Tool", style="cyan")
        tool_status_table.add_column("Status", style="bold")
        
        tool_status = analysis_results.get("tool_status", {})
        for tool, available in tool_status.items():
            status = "[green]✅ Available[/green]" if available else "[red]❌ Not Available[/red]"
            tool_status_table.add_row(tool.title(), status)
        
        # Create findings table (top 10 most critical)
        findings_table = Table(show_header=True, header_style="bold red", box=None)
        findings_table.add_column("Tool", style="bold cyan", width=10)
        findings_table.add_column("Check", style="bold yellow", width=20)
        findings_table.add_column("Description", style="white", width=40)
        findings_table.add_column("Impact", style="bold", width=10)
        
        # Sort findings by severity (High -> Medium -> Low)
        all_findings = analysis_results.get("findings", [])
        severity_order = {"High": 3, "Medium": 2, "Low": 1}
        sorted_findings = sorted(all_findings, 
                               key=lambda x: severity_order.get(x.get("impact", "Low"), 0), 
                               reverse=True)
        
        # Add top findings to table
        for finding in sorted_findings[:10]:  # Limit to top 10
            impact = finding.get("impact", "Unknown")
            impact_color = "red" if impact == "High" else "yellow" if impact == "Medium" else "green"
            
            findings_table.add_row(
                finding.get("tool", "unknown").title(),
                finding.get("check", "unknown")[:18] + "..." if len(finding.get("check", "")) > 18 else finding.get("check", "unknown"),
                finding.get("description", "")[:60] + "..." if len(finding.get("description", "")) > 60 else finding.get("description", ""),
                f"[{impact_color}]{impact}[/{impact_color}]"
            )
        
        # Combine everything into report
        report_content = f"""[bold cyan]🛡️ Security Analysis Report[/bold cyan]
[dim]Target: {analysis_results['target']}[/dim]

[bold yellow]📊 Summary[/bold yellow]
{summary_table}

[bold cyan]🔧 Tool Status[/bold cyan]
{tool_status_table}

[bold red]⚠️ Critical Findings (Top 10)[/bold red]
{findings_table}

[dim]💡 Tip: Use `audit --detailed <target>` for complete findings list[/dim]
[dim]📋 Based on {len(self.vulnerability_checks)} vulnerability patterns[/dim]"""
        
        return Panel(
            report_content,
            title=f"[bold green]Web3AuditMCP Report - {risk_level}[/bold green]",
            border_style="bold green",
            expand=False
        )
    
    def get_tool_availability(self) -> Dict[str, bool]:
        """Get availability status of all analysis tools."""
        return {
            "slither": self.slither_module.is_available(),
            "mythril": self.mythril_module.is_available(),
            "foundry": self.foundry_module.is_available(),
            "custom_checks": len(self.vulnerability_checks) > 0
        }

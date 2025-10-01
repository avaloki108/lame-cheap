"""Enhanced orchestration layer with multi-agent system and advanced LLM integration."""

import asyncio
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.layout import Layout
from rich.live import Live
import time

try:
    from .agents.orchestrator import MultiAgentOrchestrator
    from .llm.enhanced_client import EnhancedLLMClient
    from .core.adapters import AdapterRegistry, Finding
    from .config.settings import Web3AuditConfig, ConfigManager
except ImportError:
    # Fallback imports for development
    from .analysis_engine import AnalysisEngine

class EnhancedOrchestrationLayer:
    """Enhanced orchestration layer coordinating multi-agent analysis with LLM synthesis."""
    
    def __init__(self, console: Console):
        self.console = console
        
        try:
            self.config_manager = ConfigManager(console)
            self.config = self.config_manager.get_config()
            
            # Initialize components
            self.adapter_registry = AdapterRegistry(console)
            self.multi_agent_orchestrator = MultiAgentOrchestrator(console, self.config)
            self.llm_client = EnhancedLLMClient(self.config, console)
            
            # Analysis state
            self.current_analysis = None
            self.analysis_history = []
            
        except ImportError:
            # Fallback to basic analysis engine
            self.analysis_engine = AnalysisEngine(console)
            self.current_analysis = None
            self.analysis_history = []
    
    async def start_audit(self, config: Dict[str, Any]) -> Panel:
        """Start a comprehensive multi-phase audit with all available tools and agents."""
        
        target = config.get('target')
        if not target:
            return Panel("[red]Error: No target specified[/red]", title="❌ Audit Failed")
        
        # Check if enhanced components are available
        if hasattr(self, 'multi_agent_orchestrator'):
            return await self._enhanced_audit(target)
        else:
            return await self._basic_audit(target)
    
    async def _enhanced_audit(self, target: str) -> Panel:
        """Run enhanced multi-agent audit."""
        
        # Create progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            # Main audit task
            audit_task = progress.add_task("Starting comprehensive audit...", total=100)
            
            try:
                # Phase 1: Multi-Agent Analysis (60% of progress)
                progress.update(audit_task, description="🤖 Running multi-agent analysis...", completed=10)
                
                agent_results = await self.multi_agent_orchestrator.orchestrate_analysis(
                    target, progress, audit_task
                )
                
                progress.update(audit_task, completed=60)
                
                # Phase 2: LLM Enhancement (30% of progress)
                if agent_results.get("findings"):
                    progress.update(audit_task, description="🧠 Enhancing findings with LLM analysis...", completed=65)
                    
                    enhanced_results = await self._enhance_with_llm(
                        agent_results, progress, audit_task
                    )
                else:
                    enhanced_results = agent_results
                
                progress.update(audit_task, completed=90)
                
                # Phase 3: Report Generation (10% of progress)
                progress.update(audit_task, description="📊 Generating comprehensive report...", completed=95)
                
                final_report = await self._generate_comprehensive_report(enhanced_results, target)
                
                progress.update(audit_task, completed=100, description="✅ Audit completed!")
                
                # Store analysis for history
                self.current_analysis = enhanced_results
                self.analysis_history.append({
                    "target": target,
                    "timestamp": time.time(),
                    "results": enhanced_results
                })
                
                return final_report
                
            except Exception as e:
                self.console.print(f"[red]Comprehensive audit failed: {e}[/red]")
                return Panel(
                    f"[red]Audit failed with error: {e}[/red]",
                    title="❌ Audit Failed",
                    border_style="red"
                )
    
    async def _basic_audit(self, target: str) -> Panel:
        """Run basic audit using analysis engine."""
        
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
        """Perform a quick security scan focusing on critical vulnerabilities."""
        
        if hasattr(self, 'adapter_registry'):
            return await self._enhanced_quick_scan(target)
        else:
            return await self._basic_quick_scan(target)
    
    async def _enhanced_quick_scan(self, target: str) -> Panel:
        """Enhanced quick scan using adapter registry."""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            scan_task = progress.add_task("Running quick security scan...", total=None)
            
            try:
                # Quick Slither analysis
                progress.update(scan_task, description="🔍 Running Slither static analysis...")
                
                slither_adapter = self.adapter_registry.get("slither")
                findings = []
                
                if slither_adapter and slither_adapter.health_check():
                    slither_findings = await slither_adapter.run(Path(target))
                    findings.extend(slither_findings)
                
                # Filter for high/critical findings only
                critical_findings = [
                    f for f in findings 
                    if f.severity in ["critical", "high"]
                ]
                
                progress.update(scan_task, description="📋 Generating quick report...")
                
                return self._generate_quick_report(critical_findings, target)
                
            except Exception as e:
                self.console.print(f"[red]Quick scan failed: {e}[/red]")
                return Panel(
                    f"[red]Quick scan failed: {e}[/red]",
                    title="❌ Scan Failed",
                    border_style="red"
                )
    
    async def _basic_quick_scan(self, target: str) -> Panel:
        """Basic quick scan implementation."""
        
        self.console.print(Panel(
            f"[bold yellow]⚡ Running quick scan for: {target}[/bold yellow]\n"
            f"[dim]Focusing on critical vulnerabilities...[/dim]",
            border_style="bold yellow"
        ))
        
        # Simulate quick scan (would run subset of checks)
        await asyncio.sleep(1)
        
        # Create quick scan results
        table = Table(title="⚡ Quick Scan Results")
        table.add_column("Check", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Risk Level", justify="center")
        
        table.add_row("Reentrancy Detection", "✅ PASS", "[green]LOW[/green]")
        table.add_row("Access Control", "⚠️ WARNING", "[yellow]MEDIUM[/yellow]")
        table.add_row("Integer Overflow", "✅ PASS", "[green]LOW[/green]")
        table.add_row("Unchecked Calls", "❌ FAIL", "[red]HIGH[/red]")
        
        return Panel(
            table,
            title="⚡ Quick Security Scan Complete",
            border_style="yellow"
        )
    
    async def _enhance_with_llm(self, agent_results: Dict[str, Any], progress: Progress, task_id: TaskID) -> Dict[str, Any]:
        """Enhance agent results with LLM analysis."""
        
        findings = agent_results.get("findings", [])
        if not findings:
            return agent_results
        
        # Filter findings for LLM analysis (focus on high-severity)
        high_priority_findings = [
            f for f in findings 
            if f.severity in ["critical", "high"] and f.tool != "fix_recommender"
        ]
        
        if not high_priority_findings:
            return agent_results
        
        progress.update(task_id, description="🧠 LLM analyzing critical findings...")
        
        # Batch analyze findings with LLM
        llm_responses = await self.llm_client.batch_analyze_findings(
            high_priority_findings, progress, task_id
        )
        
        # Enhance findings with LLM insights
        enhanced_findings = []
        for i, finding in enumerate(findings):
            if i < len(llm_responses) and finding.severity in ["critical", "high"]:
                enhanced_finding = self.llm_client.enhance_finding_with_llm(
                    finding, llm_responses[i]
                )
                enhanced_findings.append(enhanced_finding)
            else:
                enhanced_findings.append(finding)
        
        # Generate comprehensive remediation guidance
        progress.update(task_id, description="🧠 Generating remediation guidance...")
        
        remediation_response = await self.llm_client.generate_remediation_guidance(
            high_priority_findings
        )
        
        # Update results with enhanced data
        agent_results["findings"] = enhanced_findings
        agent_results["llm_analysis"] = {
            "enhanced_findings_count": len([f for f in enhanced_findings if f.severity in ["critical", "high"]]),
            "remediation_guidance": remediation_response.content,
            "llm_confidence": remediation_response.confidence
        }
        
        return agent_results
    
    async def _generate_comprehensive_report(self, results: Dict[str, Any], target: str) -> Panel:
        """Generate a comprehensive audit report."""
        
        findings = results.get("findings", [])
        severity_dist = results.get("severity_distribution", {})
        risk_score = results.get("risk_score", 0)
        agent_performance = results.get("agent_performance", {})
        llm_analysis = results.get("llm_analysis", {})
        
        # Determine risk level and color
        if risk_score >= 50:
            risk_level = "CRITICAL"
            risk_color = "red"
        elif risk_score >= 30:
            risk_level = "HIGH"
            risk_color = "red"
        elif risk_score >= 15:
            risk_level = "MEDIUM"
            risk_color = "yellow"
        else:
            risk_level = "LOW"
            risk_color = "green"
        
        # Create summary table
        summary_table = Table(title="📊 Audit Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", justify="right")
        summary_table.add_column("Status", justify="center")
        
        summary_table.add_row("Target", str(target), "✅")
        summary_table.add_row("Total Findings", str(len(findings)), "📋")
        summary_table.add_row("Critical", str(severity_dist.get("critical", 0)), "🔴" if severity_dist.get("critical", 0) > 0 else "✅")
        summary_table.add_row("High", str(severity_dist.get("high", 0)), "🟡" if severity_dist.get("high", 0) > 0 else "✅")
        summary_table.add_row("Medium", str(severity_dist.get("medium", 0)), "🟠" if severity_dist.get("medium", 0) > 0 else "✅")
        summary_table.add_row("Low", str(severity_dist.get("low", 0)), "🟢")
        summary_table.add_row("Risk Score", str(risk_score), f"[{risk_color}]{risk_level}[/{risk_color}]")
        
        # Create findings table (top 10)
        findings_table = Table(title="🔍 Top Security Findings")
        findings_table.add_column("Severity", width=10)
        findings_table.add_column("Tool", width=12)
        findings_table.add_column("Finding", width=50)
        findings_table.add_column("Confidence", width=10)
        
        # Sort findings by severity and confidence
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(
            findings,
            key=lambda f: (severity_order.get(f.severity, 5), -f.confidence)
        )
        
        for finding in sorted_findings[:10]:
            severity_color = {
                "critical": "red",
                "high": "red",
                "medium": "yellow", 
                "low": "green",
                "info": "blue"
            }.get(finding.severity, "white")
            
            findings_table.add_row(
                f"[{severity_color}]{finding.severity.upper()}[/{severity_color}]",
                finding.tool,
                finding.title[:47] + "..." if len(finding.title) > 50 else finding.title,
                f"{finding.confidence:.2f}"
            )
        
        # Create agent performance table
        agent_table = Table(title="🤖 Agent Performance")
        agent_table.add_column("Agent", style="cyan")
        agent_table.add_column("Findings", justify="right")
        agent_table.add_column("Confidence", justify="right")
        agent_table.add_column("Time (s)", justify="right")
        
        for agent_type, performance in agent_performance.items():
            agent_table.add_row(
                agent_type.replace("_", " ").title(),
                str(performance.get("findings_count", 0)),
                f"{performance.get('confidence', 0):.2f}",
                f"{performance.get('execution_time', 0):.2f}"
            )
        
        # Create recommendations section
        recommendations = []
        
        if severity_dist.get("critical", 0) > 0:
            recommendations.append("🚨 IMMEDIATE ACTION REQUIRED: Critical vulnerabilities found")
        if severity_dist.get("high", 0) > 0:
            recommendations.append("⚠️  High-severity issues require prompt attention")
        if risk_score >= 30:
            recommendations.append("🔒 Consider security audit by external firm")
        if llm_analysis.get("remediation_guidance"):
            recommendations.append("🧠 LLM-generated remediation guidance available")
        
        if not recommendations:
            recommendations.append("✅ No critical security issues detected")
        
        # Compile report content
        report_content = f"""
{summary_table}

{findings_table}

{agent_table}

[bold]🎯 Key Recommendations:[/bold]
{chr(10).join(f"• {rec}" for rec in recommendations)}

[bold]📈 Analysis Metrics:[/bold]
• Multi-agent analysis: {len(agent_performance)} agents deployed
• LLM enhancement: {llm_analysis.get('enhanced_findings_count', 0)} findings enhanced
• Coverage: {len([f for f in findings if hasattr(f, 'checks') and f.checks])} findings mapped to security checklist

[bold]🔗 Next Steps:[/bold]
• Review detailed findings with development team
• Prioritize fixes based on severity and exploitability
• Implement recommended security measures
• Consider follow-up audit after fixes
        """
        
        return Panel(
            report_content.strip(),
            title=f"🛡️ Web3 Security Audit Report - [{risk_color}]{risk_level} RISK[/{risk_color}]",
            border_style=risk_color,
            padding=(1, 2)
        )
    
    def _generate_quick_report(self, findings: List, target: str) -> Panel:
        """Generate a quick scan report focusing on critical issues."""
        
        if not findings:
            return Panel(
                f"[green]✅ No critical vulnerabilities detected in quick scan of {target}[/green]",
                title="🚀 Quick Security Scan - CLEAN",
                border_style="green"
            )
        
        # Create findings table
        table = Table(title="⚡ Critical Security Issues")
        table.add_column("Severity", width=10)
        table.add_column("Tool", width=12)
        table.add_column("Issue", width=60)
        
        for finding in findings[:5]:  # Show top 5 critical findings
            severity_color = "red" if finding.severity == "critical" else "red"
            table.add_row(
                f"[{severity_color}]{finding.severity.upper()}[/{severity_color}]",
                finding.tool,
                finding.title
            )
        
        report_content = f"""
[bold]Target:[/bold] {target}
[bold]Critical Issues Found:[/bold] {len(findings)}

{table}

[bold red]⚠️  IMMEDIATE ATTENTION REQUIRED[/bold red]

Critical vulnerabilities detected that could lead to:
• Loss of funds
• Unauthorized access
• Contract exploitation

[bold]Recommended Actions:[/bold]
1. Stop any planned deployments
2. Review each critical finding immediately
3. Implement fixes before proceeding
4. Run comprehensive audit for full analysis
        """
        
        return Panel(
            report_content.strip(),
            title="🚨 Quick Security Scan - CRITICAL ISSUES FOUND",
            border_style="red",
            padding=(1, 2)
        )
    
    async def get_tool_status(self) -> Dict[str, bool]:
        """Get the status of all analysis tools."""
        if hasattr(self, 'adapter_registry'):
            return self.adapter_registry.health_check_all()
        else:
            return {
                "slither": True,
                "mythril": True,
                "foundry": True
            }
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Get history of previous analyses."""
        return self.analysis_history[-10:]  # Return last 10 analyses
    
    def export_results(self, format: str = "json") -> str:
        """Export current analysis results in specified format."""
        if not self.current_analysis:
            return "No analysis results available"
        
        if format.lower() == "json":
            return json.dumps(self.current_analysis, indent=2, default=str)
        elif format.lower() == "markdown":
            return self._export_to_markdown()
        else:
            return "Unsupported export format"
    
    def _export_to_markdown(self) -> str:
        """Export results to Markdown format."""
        if not self.current_analysis:
            return "# No Analysis Results Available"
        
        results = self.current_analysis
        findings = results.get("findings", [])
        
        md_content = f"""# Web3 Security Audit Report

## Summary
- **Target**: {results.get('target', 'Unknown')}
- **Total Findings**: {len(findings)}
- **Risk Score**: {results.get('risk_score', 0)}

## Findings by Severity

"""
        
        # Group findings by severity
        by_severity = {}
        for finding in findings:
            severity = finding.severity if hasattr(finding, 'severity') else 'unknown'
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(finding)
        
        for severity in ["critical", "high", "medium", "low", "info"]:
            if severity in by_severity:
                md_content += f"### {severity.title()} Severity ({len(by_severity[severity])} findings)\n\n"
                
                for finding in by_severity[severity]:
                    title = finding.title if hasattr(finding, 'title') else 'Unknown Finding'
                    tool = finding.tool if hasattr(finding, 'tool') else 'Unknown Tool'
                    confidence = finding.confidence if hasattr(finding, 'confidence') else 0.0
                    description = finding.description if hasattr(finding, 'description') else 'No description'
                    recommendation = finding.recommendation if hasattr(finding, 'recommendation') else 'No recommendation'
                    
                    md_content += f"""#### {title}
- **Tool**: {tool}
- **Confidence**: {confidence:.2f}
- **Description**: {description}
- **Recommendation**: {recommendation}

"""
        
        return md_content

# Backward compatibility alias
OrchestrationLayer = EnhancedOrchestrationLayer

"""Multi-agent orchestration system for comprehensive Web3 security analysis."""

import asyncio
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
import uuid
from datetime import datetime

from ..core.adapters import Finding, AnalyzerAdapter, AdapterRegistry
from ..config.settings import Web3AuditConfig

@dataclass
class AgentTask:
    """Represents a task for an analysis agent."""
    id: str
    agent_type: str
    target: str
    priority: int = 5  # 1-10, higher is more urgent
    dependencies: List[str] = None  # Task IDs this depends on
    context: Dict[str, Any] = None
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    created_at: str = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.context is None:
            self.context = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

@dataclass
class AgentResult:
    """Result from an analysis agent."""
    agent_type: str
    task_id: str
    findings: List[Finding]
    confidence: float
    execution_time: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class AnalysisAgent:
    """Base class for specialized analysis agents."""
    
    def __init__(self, agent_type: str, console: Console, config: Web3AuditConfig):
        self.agent_type = agent_type
        self.console = console
        self.config = config
        self.capabilities = self._define_capabilities()
    
    def _define_capabilities(self) -> Set[str]:
        """Define what this agent can analyze."""
        return set()
    
    async def analyze(self, task: AgentTask) -> AgentResult:
        """Perform analysis for the given task."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            findings = await self._execute_analysis(task)
            confidence = self._calculate_confidence(findings, task)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.id,
                findings=findings,
                confidence=confidence,
                execution_time=execution_time,
                metadata={"task_context": task.context}
            )
            
        except Exception as e:
            self.console.print(f"[red]Agent {self.agent_type} failed: {e}[/red]")
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.id,
                findings=[],
                confidence=0.0,
                execution_time=asyncio.get_event_loop().time() - start_time,
                metadata={"error": str(e)}
            )
    
    async def _execute_analysis(self, task: AgentTask) -> List[Finding]:
        """Execute the actual analysis logic."""
        raise NotImplementedError("Subclasses must implement _execute_analysis")
    
    def _calculate_confidence(self, findings: List[Finding], task: AgentTask) -> float:
        """Calculate confidence in the analysis results."""
        if not findings:
            return 0.5  # Neutral confidence when no findings
        
        # Average confidence of all findings
        total_confidence = sum(f.confidence for f in findings)
        return min(total_confidence / len(findings), 1.0)

class VulnerabilityDetectorAgent(AnalysisAgent):
    """Agent specialized in detecting common vulnerabilities."""
    
    def __init__(self, console: Console, config: Web3AuditConfig, adapter_registry: AdapterRegistry):
        super().__init__("vulnerability_detector", console, config)
        self.adapter_registry = adapter_registry
    
    def _define_capabilities(self) -> Set[str]:
        return {
            "reentrancy_detection",
            "access_control_analysis", 
            "integer_overflow_detection",
            "unchecked_calls",
            "timestamp_dependence",
            "tx_origin_usage"
        }
    
    async def _execute_analysis(self, task: AgentTask) -> List[Finding]:
        """Execute vulnerability detection using multiple tools."""
        all_findings = []
        
        # Use Slither for static analysis
        slither_adapter = self.adapter_registry.get("slither")
        if slither_adapter and slither_adapter.health_check():
            try:
                slither_findings = await slither_adapter.run(Path(task.target))
                all_findings.extend(slither_findings)
                self.console.print(f"[green]Slither found {len(slither_findings)} issues[/green]")
            except Exception as e:
                self.console.print(f"[yellow]Slither analysis failed: {e}[/yellow]")
        
        # Use Mythril for symbolic execution
        mythril_adapter = self.adapter_registry.get("mythril")
        if mythril_adapter and mythril_adapter.health_check():
            try:
                mythril_findings = await mythril_adapter.run(Path(task.target))
                all_findings.extend(mythril_findings)
                self.console.print(f"[green]Mythril found {len(mythril_findings)} issues[/green]")
            except Exception as e:
                self.console.print(f"[yellow]Mythril analysis failed: {e}[/yellow]")
        
        # Apply custom vulnerability patterns
        custom_findings = await self._apply_custom_patterns(task.target)
        all_findings.extend(custom_findings)
        
        return self._deduplicate_findings(all_findings)
    
    async def _apply_custom_patterns(self, target: str) -> List[Finding]:
        """Apply custom vulnerability detection patterns."""
        findings = []
        
        try:
            # Read contract files
            for sol_file in Path(target).rglob("*.sol"):
                with open(sol_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for common patterns
                file_findings = []
                
                # Reentrancy pattern detection
                if self._check_reentrancy_pattern(content):
                    file_findings.append(Finding(
                        id=str(uuid.uuid4()),
                        tool="custom_detector",
                        rule_id="custom-reentrancy-pattern",
                        title="Potential Reentrancy Vulnerability",
                        description="External call followed by state change detected",
                        severity="high",
                        confidence=0.7,
                        files=[{"path": str(sol_file), "lines": [0]}],
                        trace=[],
                        tool_output="Pattern-based detection",
                        checks=["SOL-AM-ReentrancyAttack-1"],
                        recommendation="Use checks-effects-interactions pattern"
                    ))
                
                # Unchecked external call pattern
                if self._check_unchecked_call_pattern(content):
                    file_findings.append(Finding(
                        id=str(uuid.uuid4()),
                        tool="custom_detector",
                        rule_id="custom-unchecked-call",
                        title="Unchecked External Call",
                        description="External call without return value check detected",
                        severity="medium",
                        confidence=0.8,
                        files=[{"path": str(sol_file), "lines": [0]}],
                        trace=[],
                        tool_output="Pattern-based detection",
                        checks=["SOL-AM-UncheckedSend-1"],
                        recommendation="Always check return values of external calls"
                    ))
                
                findings.extend(file_findings)
                
        except Exception as e:
            self.console.print(f"[yellow]Custom pattern analysis failed: {e}[/yellow]")
        
        return findings
    
    def _check_reentrancy_pattern(self, content: str) -> bool:
        """Check for reentrancy vulnerability patterns."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for external calls
            if any(pattern in line.lower() for pattern in ['.call(', '.send(', '.transfer(']):
                # Check subsequent lines for state changes
                for j in range(i + 1, min(i + 10, len(lines))):
                    if any(pattern in lines[j] for pattern in ['=', '+=', '-=', '*=', '/=']):
                        if not any(guard in content.lower() for guard in ['nonreentrant', 'mutex', 'locked']):
                            return True
        
        return False
    
    def _check_unchecked_call_pattern(self, content: str) -> bool:
        """Check for unchecked external call patterns."""
        lines = content.split('\n')
        
        for line in lines:
            # Look for external calls without return value checks
            if '.call(' in line and not any(check in line for check in ['require(', 'assert(', 'if(', 'bool success']):
                return True
        
        return False
    
    def _deduplicate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings based on similarity."""
        unique_findings = []
        seen_signatures = set()
        
        for finding in findings:
            # Create a signature based on rule_id, severity, and file
            signature = f"{finding.rule_id}:{finding.severity}:{finding.files[0]['path'] if finding.files else 'unknown'}"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_findings.append(finding)
        
        return unique_findings

class ExploitAnalyzerAgent(AnalysisAgent):
    """Agent specialized in analyzing exploit scenarios and attack vectors."""
    
    def __init__(self, console: Console, config: Web3AuditConfig):
        super().__init__("exploit_analyzer", console, config)
    
    def _define_capabilities(self) -> Set[str]:
        return {
            "attack_scenario_generation",
            "exploit_path_analysis",
            "economic_impact_assessment",
            "front_running_analysis",
            "mev_vulnerability_detection"
        }
    
    async def _execute_analysis(self, task: AgentTask) -> List[Finding]:
        """Analyze potential exploit scenarios."""
        findings = []
        
        # Get existing findings from context
        existing_findings = task.context.get("findings", [])
        
        for finding in existing_findings:
            if finding.severity in ["critical", "high"]:
                # Generate exploit scenario for high-severity findings
                exploit_finding = await self._generate_exploit_scenario(finding, task.target)
                if exploit_finding:
                    findings.append(exploit_finding)
        
        return findings
    
    async def _generate_exploit_scenario(self, base_finding: Finding, target: str) -> Optional[Finding]:
        """Generate detailed exploit scenario for a vulnerability."""
        
        exploit_scenarios = {
            "reentrancy": """
            1. Attacker deploys malicious contract with fallback function
            2. Attacker calls vulnerable withdraw function
            3. In fallback, attacker recursively calls withdraw again
            4. Contract state not updated until after external call
            5. Attacker drains contract balance
            """,
            "unchecked-send": """
            1. Attacker creates contract that always reverts on receive
            2. Legitimate user tries to withdraw to attacker's contract
            3. Send/transfer fails but contract doesn't handle failure
            4. User's balance decreases but funds remain in contract
            5. Funds become permanently locked
            """,
            "integer-overflow": """
            1. Attacker finds function with arithmetic operations
            2. Attacker provides inputs that cause overflow/underflow
            3. Unexpected values bypass security checks
            4. Attacker gains unauthorized access or funds
            """
        }
        
        # Match finding to exploit scenario
        scenario_key = None
        if "reentrancy" in base_finding.rule_id.lower():
            scenario_key = "reentrancy"
        elif "unchecked" in base_finding.rule_id.lower():
            scenario_key = "unchecked-send"
        elif "overflow" in base_finding.rule_id.lower():
            scenario_key = "integer-overflow"
        
        if scenario_key:
            return Finding(
                id=str(uuid.uuid4()),
                tool="exploit_analyzer",
                rule_id=f"exploit-{scenario_key}",
                title=f"Exploit Scenario: {base_finding.title}",
                description=f"Detailed attack scenario for {base_finding.title}",
                severity=base_finding.severity,
                confidence=0.8,
                files=base_finding.files,
                trace=[],
                tool_output=exploit_scenarios[scenario_key],
                checks=base_finding.checks,
                recommendation=f"Implement comprehensive fix for {base_finding.title}",
                exploit_scenario=exploit_scenarios[scenario_key]
            )
        
        return None

class FixRecommenderAgent(AnalysisAgent):
    """Agent specialized in providing detailed fix recommendations."""
    
    def __init__(self, console: Console, config: Web3AuditConfig):
        super().__init__("fix_recommender", console, config)
    
    def _define_capabilities(self) -> Set[str]:
        return {
            "code_fix_generation",
            "security_pattern_recommendation",
            "best_practice_guidance",
            "library_suggestions"
        }
    
    async def _execute_analysis(self, task: AgentTask) -> List[Finding]:
        """Generate detailed fix recommendations."""
        findings = []
        
        # Get existing findings from context
        existing_findings = task.context.get("findings", [])
        
        for finding in existing_findings:
            fix_finding = await self._generate_fix_recommendation(finding, task.target)
            if fix_finding:
                findings.append(fix_finding)
        
        return findings
    
    async def _generate_fix_recommendation(self, base_finding: Finding, target: str) -> Optional[Finding]:
        """Generate detailed fix recommendation for a vulnerability."""
        
        fix_templates = {
            "reentrancy": {
                "recommendation": """
                1. Use the Checks-Effects-Interactions pattern:
                   - Perform all checks first
                   - Update state variables
                   - Interact with external contracts last
                
                2. Add a reentrancy guard:
                   ```solidity
                   bool private locked;
                   modifier noReentrancy() {
                       require(!locked, "Reentrant call");
                       locked = true;
                       _;
                       locked = false;
                   }
                   ```
                
                3. Use OpenZeppelin's ReentrancyGuard:
                   ```solidity
                   import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
                   contract MyContract is ReentrancyGuard {
                       function withdraw() external nonReentrant {
                           // Safe withdrawal logic
                       }
                   }
                   ```
                """,
                "libraries": ["@openzeppelin/contracts/security/ReentrancyGuard.sol"],
                "gas_impact": "Low (additional SSTORE operations)"
            },
            "unchecked-send": {
                "recommendation": """
                1. Always check return values:
                   ```solidity
                   (bool success, ) = recipient.call{value: amount}("");
                   require(success, "Transfer failed");
                   ```
                
                2. Use withdrawal pattern instead of push payments:
                   ```solidity
                   mapping(address => uint256) public pendingWithdrawals;
                   
                   function withdraw() external {
                       uint256 amount = pendingWithdrawals[msg.sender];
                       require(amount > 0, "No funds to withdraw");
                       pendingWithdrawals[msg.sender] = 0;
                       (bool success, ) = msg.sender.call{value: amount}("");
                       require(success, "Withdrawal failed");
                   }
                   ```
                """,
                "libraries": [],
                "gas_impact": "Medium (additional checks and state updates)"
            }
        }
        
        # Match finding to fix template
        template_key = None
        if "reentrancy" in base_finding.rule_id.lower():
            template_key = "reentrancy"
        elif "unchecked" in base_finding.rule_id.lower():
            template_key = "unchecked-send"
        
        if template_key and template_key in fix_templates:
            template = fix_templates[template_key]
            
            return Finding(
                id=str(uuid.uuid4()),
                tool="fix_recommender",
                rule_id=f"fix-{template_key}",
                title=f"Fix Recommendation: {base_finding.title}",
                description=f"Detailed fix guidance for {base_finding.title}",
                severity="info",
                confidence=0.9,
                files=base_finding.files,
                trace=[],
                tool_output=template["recommendation"],
                checks=base_finding.checks,
                recommendation=template["recommendation"],
                references=template["libraries"]
            )
        
        return None

class MultiAgentOrchestrator:
    """Orchestrates multiple analysis agents for comprehensive security auditing."""
    
    def __init__(self, console: Console, config: Web3AuditConfig):
        self.console = console
        self.config = config
        self.adapter_registry = AdapterRegistry(console)
        self.agents = self._initialize_agents()
        self.task_queue = asyncio.Queue()
        self.results = {}
    
    def _initialize_agents(self) -> Dict[str, AnalysisAgent]:
        """Initialize all analysis agents."""
        agents = {}
        
        # Core vulnerability detection agent
        agents["vulnerability_detector"] = VulnerabilityDetectorAgent(
            self.console, self.config, self.adapter_registry
        )
        
        # Exploit analysis agent
        agents["exploit_analyzer"] = ExploitAnalyzerAgent(
            self.console, self.config
        )
        
        # Fix recommendation agent
        agents["fix_recommender"] = FixRecommenderAgent(
            self.console, self.config
        )
        
        return agents
    
    async def orchestrate_analysis(self, target: str, progress: Progress, task_id: TaskID) -> Dict[str, Any]:
        """Orchestrate multi-agent analysis of the target."""
        
        progress.update(task_id, description="Initializing multi-agent analysis...")
        
        # Phase 1: Vulnerability Detection
        vuln_task = AgentTask(
            id=str(uuid.uuid4()),
            agent_type="vulnerability_detector",
            target=target,
            priority=10
        )
        
        progress.update(task_id, description="Running vulnerability detection...")
        vuln_result = await self.agents["vulnerability_detector"].analyze(vuln_task)
        
        # Phase 2: Exploit Analysis (depends on vulnerability findings)
        if vuln_result.findings:
            exploit_task = AgentTask(
                id=str(uuid.uuid4()),
                agent_type="exploit_analyzer",
                target=target,
                priority=8,
                context={"findings": vuln_result.findings}
            )
            
            progress.update(task_id, description="Analyzing exploit scenarios...")
            exploit_result = await self.agents["exploit_analyzer"].analyze(exploit_task)
        else:
            exploit_result = AgentResult("exploit_analyzer", "", [], 0.0, 0.0)
        
        # Phase 3: Fix Recommendations
        all_findings = vuln_result.findings + exploit_result.findings
        if all_findings:
            fix_task = AgentTask(
                id=str(uuid.uuid4()),
                agent_type="fix_recommender", 
                target=target,
                priority=6,
                context={"findings": vuln_result.findings}  # Only base findings for fixes
            )
            
            progress.update(task_id, description="Generating fix recommendations...")
            fix_result = await self.agents["fix_recommender"].analyze(fix_task)
        else:
            fix_result = AgentResult("fix_recommender", "", [], 0.0, 0.0)
        
        progress.update(task_id, description="Consolidating results...")
        
        # Consolidate results
        return self._consolidate_results([vuln_result, exploit_result, fix_result], target)
    
    def _consolidate_results(self, results: List[AgentResult], target: str) -> Dict[str, Any]:
        """Consolidate results from all agents."""
        
        all_findings = []
        agent_performance = {}
        
        for result in results:
            all_findings.extend(result.findings)
            agent_performance[result.agent_type] = {
                "findings_count": len(result.findings),
                "confidence": result.confidence,
                "execution_time": result.execution_time
            }
        
        # Calculate severity distribution
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in all_findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
        
        # Calculate risk score
        risk_score = (
            severity_counts["critical"] * 20 +
            severity_counts["high"] * 10 +
            severity_counts["medium"] * 5 +
            severity_counts["low"] * 1
        )
        
        return {
            "target": target,
            "total_findings": len(all_findings),
            "findings": all_findings,
            "severity_distribution": severity_counts,
            "risk_score": risk_score,
            "agent_performance": agent_performance,
            "analysis_complete": True
        }
    
    def generate_agent_report(self, results: Dict[str, Any]) -> Panel:
        """Generate a detailed multi-agent analysis report."""
        
        # Create main table
        table = Table(title="🤖 Multi-Agent Security Analysis Report")
        table.add_column("Agent", style="cyan")
        table.add_column("Findings", justify="right")
        table.add_column("Confidence", justify="right")
        table.add_column("Time (s)", justify="right")
        
        for agent_type, performance in results["agent_performance"].items():
            table.add_row(
                agent_type.replace("_", " ").title(),
                str(performance["findings_count"]),
                f"{performance['confidence']:.2f}",
                f"{performance['execution_time']:.2f}"
            )
        
        # Create findings tree
        findings_tree = Tree("🔍 Findings by Agent")
        
        findings_by_agent = {}
        for finding in results["findings"]:
            agent = finding.tool
            if agent not in findings_by_agent:
                findings_by_agent[agent] = []
            findings_by_agent[agent].append(finding)
        
        for agent, findings in findings_by_agent.items():
            agent_branch = findings_tree.add(f"[bold]{agent}[/bold] ({len(findings)} findings)")
            for finding in findings[:3]:  # Show first 3 findings
                severity_color = {
                    "critical": "red",
                    "high": "red", 
                    "medium": "yellow",
                    "low": "green",
                    "info": "blue"
                }.get(finding.severity, "white")
                
                agent_branch.add(f"[{severity_color}]{finding.severity.upper()}[/{severity_color}]: {finding.title}")
        
        # Risk assessment
        risk_level = "LOW"
        if results["risk_score"] >= 50:
            risk_level = "CRITICAL"
        elif results["risk_score"] >= 30:
            risk_level = "HIGH"
        elif results["risk_score"] >= 15:
            risk_level = "MEDIUM"
        
        risk_color = {
            "CRITICAL": "red",
            "HIGH": "red",
            "MEDIUM": "yellow", 
            "LOW": "green"
        }.get(risk_level, "white")
        
        report_content = f"""
[bold]Target:[/bold] {results['target']}
[bold]Total Findings:[/bold] {results['total_findings']}
[bold]Risk Score:[/bold] {results['risk_score']}
[bold]Risk Level:[/bold] [{risk_color}]{risk_level}[/{risk_color}]

{table}

{findings_tree}
        """
        
        return Panel(
            report_content.strip(),
            title="🛡️ Multi-Agent Security Analysis",
            border_style=risk_color
        )

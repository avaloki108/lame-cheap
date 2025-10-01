"""Advanced adapter system for Web3AuditMCP inspired by production frameworks."""

import asyncio
import subprocess
import json
import tempfile
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.progress import Progress, TaskID
import uuid
from datetime import datetime

@dataclass
class AdapterConfig:
    """Configuration for analysis tool adapters."""
    cmd: str
    args: List[str]
    timeout: int = 300
    enabled: bool = True
    parallel: bool = True
    retry_count: int = 2
    environment: Dict[str, str] = None
    working_dir: Optional[str] = None
    
    def __post_init__(self):
        if self.environment is None:
            self.environment = {}

@dataclass
class Finding:
    """Canonical finding format for all analysis tools."""
    id: str
    tool: str
    rule_id: str
    title: str
    description: str
    severity: str  # "critical", "high", "medium", "low", "info"
    confidence: float  # 0.0 to 1.0
    
    # Evidence and location
    files: List[Dict[str, Any]]  # [{"path": "contract.sol", "lines": [10, 15]}]
    trace: List[str]  # Execution trace or call stack
    tool_output: str  # Raw tool output
    
    # Metadata
    checks: List[str]  # Checklist IDs this finding relates to
    recommendation: str
    gas_estimate: Optional[int] = None
    exploit_scenario: Optional[str] = None
    references: List[str] = None
    
    # Timestamps
    created_at: str = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.references is None:
            self.references = []

class AnalyzerAdapter(Protocol):
    """Protocol defining the interface for all analysis tool adapters."""
    
    name: str
    
    def discover(self, repo_path: Path) -> Dict[str, Any]:
        """Discover contracts and project structure."""
        ...
    
    async def run(self, repo_path: Path, target: Optional[str] = None, config: AdapterConfig = None) -> List[Finding]:
        """Run analysis and return normalized findings."""
        ...
    
    def health_check(self) -> bool:
        """Check if the tool is available and working."""
        ...

class BaseAdapter(ABC):
    """Base class for all analysis tool adapters."""
    
    def __init__(self, console: Console, name: str):
        self.console = console
        self.name = name
        self._cache = {}
    
    @abstractmethod
    async def run(self, repo_path: Path, target: Optional[str] = None, config: AdapterConfig = None) -> List[Finding]:
        """Run the analysis tool and return findings."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the tool is available."""
        pass
    
    def discover(self, repo_path: Path) -> Dict[str, Any]:
        """Default discovery implementation."""
        solidity_files = list(Path(repo_path).rglob("*.sol"))
        vyper_files = list(Path(repo_path).rglob("*.vy"))
        
        return {
            "solidity_files": [str(f) for f in solidity_files],
            "vyper_files": [str(f) for f in vyper_files],
            "total_contracts": len(solidity_files) + len(vyper_files),
            "project_type": self._detect_project_type(repo_path)
        }
    
    def _detect_project_type(self, repo_path: Path) -> str:
        """Detect the type of blockchain project."""
        if (repo_path / "foundry.toml").exists():
            return "foundry"
        elif (repo_path / "hardhat.config.js").exists() or (repo_path / "hardhat.config.ts").exists():
            return "hardhat"
        elif (repo_path / "truffle-config.js").exists():
            return "truffle"
        elif (repo_path / "brownie-config.yaml").exists():
            return "brownie"
        else:
            return "unknown"
    
    async def _run_command(self, cmd: List[str], config: AdapterConfig, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a command with proper error handling and timeouts."""
        env = os.environ.copy()
        env.update(config.environment)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or config.working_dir,
                env=env
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=config.timeout
            )
            
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout.decode('utf-8', errors='ignore'),
                stderr=stderr.decode('utf-8', errors='ignore')
            )
            
        except asyncio.TimeoutError:
            if process:
                process.kill()
                await process.wait()
            raise TimeoutError(f"Command timed out after {config.timeout} seconds: {' '.join(cmd)}")
    
    def _normalize_severity(self, tool_severity: str) -> str:
        """Normalize severity levels across different tools."""
        severity_map = {
            # Slither
            "high": "high",
            "medium": "medium", 
            "low": "low",
            "informational": "info",
            
            # Mythril
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            
            # Custom mappings
            "critical": "critical",
            "error": "high",
            "warning": "medium",
            "note": "low",
            "info": "info"
        }
        
        return severity_map.get(tool_severity.lower(), "medium")

class SlitherAdapter(BaseAdapter):
    """Enhanced Slither adapter with advanced features."""
    
    def __init__(self, console: Console):
        super().__init__(console, "slither")
        self.slither_path = self._find_slither()
    
    def _find_slither(self) -> Optional[str]:
        """Find Slither installation."""
        try:
            result = subprocess.run(['which', 'slither'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def health_check(self) -> bool:
        """Check if Slither is available."""
        if not self.slither_path:
            return False
        
        try:
            result = subprocess.run([self.slither_path, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    async def run(self, repo_path: Path, target: Optional[str] = None, config: AdapterConfig = None) -> List[Finding]:
        """Run Slither analysis with advanced configuration."""
        if not config:
            config = AdapterConfig(
                cmd="slither",
                args=["--json", "-", "--disable-color"],
                timeout=300
            )
        
        findings = []
        analysis_target = target or str(repo_path)
        
        try:
            cmd = [self.slither_path, analysis_target] + config.args
            result = await self._run_command(cmd, config, repo_path)
            
            if result.stdout:
                try:
                    slither_output = json.loads(result.stdout)
                    findings = self._parse_slither_output(slither_output, analysis_target)
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    findings = self._parse_text_output(result.stdout, analysis_target)
            
        except Exception as e:
            self.console.print(f"[red]Slither analysis failed: {e}[/red]")
        
        return findings
    
    def _parse_slither_output(self, slither_output: Dict[str, Any], target: str) -> List[Finding]:
        """Parse Slither JSON output into canonical findings."""
        findings = []
        
        if 'results' in slither_output and 'detectors' in slither_output['results']:
            for detector in slither_output['results']['detectors']:
                finding = Finding(
                    id=str(uuid.uuid4()),
                    tool="slither",
                    rule_id=f"slither-{detector.get('check', 'unknown')}",
                    title=detector.get('description', '').split('.')[0],
                    description=detector.get('description', ''),
                    severity=self._normalize_severity(detector.get('impact', 'medium')),
                    confidence=self._map_confidence(detector.get('confidence', 'medium')),
                    files=self._extract_file_info(detector.get('elements', [])),
                    trace=[],
                    tool_output=json.dumps(detector, indent=2),
                    checks=self._map_to_checklist(detector.get('check', '')),
                    recommendation=self._get_recommendation(detector.get('check', '')),
                    references=[]
                )
                findings.append(finding)
        
        return findings
    
    def _map_confidence(self, slither_confidence: str) -> float:
        """Map Slither confidence to float."""
        confidence_map = {
            "high": 0.9,
            "medium": 0.7,
            "low": 0.5
        }
        return confidence_map.get(slither_confidence.lower(), 0.7)
    
    def _extract_file_info(self, elements: List[Dict]) -> List[Dict[str, Any]]:
        """Extract file and line information from Slither elements."""
        files = []
        for element in elements:
            if 'source_mapping' in element:
                mapping = element['source_mapping']
                if 'filename_absolute' in mapping:
                    files.append({
                        "path": mapping['filename_absolute'],
                        "lines": [mapping.get('lines', [0])[0]] if mapping.get('lines') else [0]
                    })
        return files
    
    def _map_to_checklist(self, check_name: str) -> List[str]:
        """Map Slither check to vulnerability checklist IDs."""
        check_mapping = {
            "reentrancy-eth": ["SOL-AM-ReentrancyAttack-1", "SOL-AM-ReentrancyAttack-2"],
            "reentrancy-no-eth": ["SOL-AM-ReentrancyAttack-3"],
            "tx-origin": ["SOL-AM-TxOrigin-1"],
            "unchecked-send": ["SOL-AM-UncheckedSend-1"],
            "uninitialized-state": ["SOL-AM-UninitializedState-1"],
            "unused-return": ["SOL-AM-UnusedReturn-1"],
            "timestamp": ["SOL-AM-Timestamp-1"],
            "weak-prng": ["SOL-AM-WeakPRNG-1"]
        }
        return check_mapping.get(check_name, [])
    
    def _get_recommendation(self, check_name: str) -> str:
        """Get remediation recommendation for Slither check."""
        recommendations = {
            "reentrancy-eth": "Use the checks-effects-interactions pattern and consider adding a reentrancy guard.",
            "tx-origin": "Use msg.sender instead of tx.origin for authorization checks.",
            "unchecked-send": "Check the return value of external calls and handle failures appropriately.",
            "timestamp": "Avoid using block.timestamp for critical logic; use block numbers or external oracles.",
            "weak-prng": "Use a secure source of randomness like Chainlink VRF or commit-reveal schemes."
        }
        return recommendations.get(check_name, "Review the code and apply security best practices.")
    
    def _parse_text_output(self, text_output: str, target: str) -> List[Finding]:
        """Parse Slither text output as fallback."""
        findings = []
        lines = text_output.split('\n')
        
        current_finding = None
        for line in lines:
            line = line.strip()
            
            if 'INFO:Detectors:' in line or any(severity in line for severity in ['HIGH', 'MEDIUM', 'LOW']):
                if current_finding:
                    findings.append(current_finding)
                
                current_finding = Finding(
                    id=str(uuid.uuid4()),
                    tool="slither",
                    rule_id="slither-text-parse",
                    title=line[:100],
                    description=line,
                    severity="medium",
                    confidence=0.7,
                    files=[{"path": target, "lines": [0]}],
                    trace=[],
                    tool_output=line,
                    checks=[],
                    recommendation="Review the detected issue and apply appropriate fixes."
                )
            elif current_finding and line:
                current_finding.description += f" {line}"
                current_finding.tool_output += f"\n{line}"
        
        if current_finding:
            findings.append(current_finding)
            
        return findings

class MythrilAdapter(BaseAdapter):
    """Enhanced Mythril adapter with symbolic execution capabilities."""
    
    def __init__(self, console: Console):
        super().__init__(console, "mythril")
        self.mythril_path = self._find_mythril()
    
    def _find_mythril(self) -> Optional[str]:
        """Find Mythril installation."""
        try:
            result = subprocess.run(['which', 'myth'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def health_check(self) -> bool:
        """Check if Mythril is available."""
        if not self.mythril_path:
            return False
        
        try:
            result = subprocess.run([self.mythril_path, 'version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    async def run(self, repo_path: Path, target: Optional[str] = None, config: AdapterConfig = None) -> List[Finding]:
        """Run Mythril symbolic execution analysis."""
        if not config:
            config = AdapterConfig(
                cmd="myth",
                args=["analyze", "--output", "json", "--execution-timeout", "300"],
                timeout=400
            )
        
        findings = []
        
        # Find Solidity files to analyze
        sol_files = list(Path(repo_path).rglob("*.sol"))
        if target:
            sol_files = [Path(target)] if Path(target).suffix == ".sol" else sol_files
        
        for sol_file in sol_files[:3]:  # Limit to first 3 files for performance
            try:
                cmd = [self.mythril_path] + config.args + [str(sol_file)]
                result = await self._run_command(cmd, config, repo_path)
                
                if result.stdout:
                    try:
                        mythril_output = json.loads(result.stdout)
                        file_findings = self._parse_mythril_output(mythril_output, str(sol_file))
                        findings.extend(file_findings)
                    except json.JSONDecodeError:
                        file_findings = self._parse_mythril_text(result.stdout, str(sol_file))
                        findings.extend(file_findings)
                        
            except Exception as e:
                self.console.print(f"[red]Mythril analysis failed for {sol_file}: {e}[/red]")
        
        return findings
    
    def _parse_mythril_output(self, mythril_output: Union[Dict, List], target: str) -> List[Finding]:
        """Parse Mythril JSON output into canonical findings."""
        findings = []
        
        issues = []
        if isinstance(mythril_output, dict):
            if 'issues' in mythril_output:
                issues = mythril_output['issues']
            elif mythril_output.get('success') and mythril_output.get('issues'):
                issues = mythril_output['issues']
            else:
                issues = [mythril_output] if mythril_output else []
        elif isinstance(mythril_output, list):
            issues = mythril_output
        
        for issue in issues:
            if isinstance(issue, dict):
                finding = Finding(
                    id=str(uuid.uuid4()),
                    tool="mythril",
                    rule_id=f"mythril-{issue.get('swc-id', 'unknown')}",
                    title=issue.get('title', 'Mythril Detection'),
                    description=issue.get('description', ''),
                    severity=self._normalize_severity(issue.get('severity', 'medium')),
                    confidence=0.8,  # Mythril doesn't provide confidence
                    files=[{
                        "path": issue.get('filename', target),
                        "lines": [issue.get('lineno', 0)]
                    }],
                    trace=issue.get('debug', '').split('\n') if issue.get('debug') else [],
                    tool_output=json.dumps(issue, indent=2),
                    checks=self._map_mythril_to_checklist(issue.get('swc-id', '')),
                    recommendation=self._get_mythril_recommendation(issue.get('swc-id', '')),
                    references=[]
                )
                findings.append(finding)
        
        return findings
    
    def _map_mythril_to_checklist(self, swc_id: str) -> List[str]:
        """Map Mythril SWC IDs to vulnerability checklist."""
        swc_mapping = {
            "SWC-107": ["SOL-AM-ReentrancyAttack-1"],
            "SWC-101": ["SOL-AM-IntegerOverflow-1"],
            "SWC-104": ["SOL-AM-UncheckedSend-1"],
            "SWC-105": ["SOL-AM-UnprotectedEther-1"],
            "SWC-106": ["SOL-AM-UnprotectedSelfDestruct-1"],
            "SWC-115": ["SOL-AM-TxOrigin-1"]
        }
        return swc_mapping.get(swc_id, [])
    
    def _get_mythril_recommendation(self, swc_id: str) -> str:
        """Get remediation recommendation for Mythril SWC ID."""
        recommendations = {
            "SWC-107": "Implement reentrancy guards and follow checks-effects-interactions pattern.",
            "SWC-101": "Use SafeMath library or Solidity 0.8+ built-in overflow protection.",
            "SWC-104": "Always check return values of external calls.",
            "SWC-105": "Implement proper access controls for withdrawal functions.",
            "SWC-106": "Restrict selfdestruct calls to authorized users only.",
            "SWC-115": "Use msg.sender instead of tx.origin for authorization."
        }
        return recommendations.get(swc_id, "Review the vulnerability and implement appropriate security measures.")
    
    def _parse_mythril_text(self, text_output: str, target: str) -> List[Finding]:
        """Parse Mythril text output as fallback."""
        findings = []
        lines = text_output.split('\n')
        
        current_finding = None
        for line in lines:
            line = line.strip()
            
            if line.startswith('==== ') and line.endswith(' ===='):
                if current_finding:
                    findings.append(current_finding)
                
                title = line.replace('====', '').strip()
                current_finding = Finding(
                    id=str(uuid.uuid4()),
                    tool="mythril",
                    rule_id="mythril-text-parse",
                    title=title,
                    description=title,
                    severity="medium",
                    confidence=0.8,
                    files=[{"path": target, "lines": [0]}],
                    trace=[],
                    tool_output=title,
                    checks=[],
                    recommendation="Review the detected vulnerability and implement fixes."
                )
            elif current_finding and line:
                if line.startswith('SWC ID:'):
                    swc_id = line.replace('SWC ID:', '').strip()
                    current_finding.rule_id = f"mythril-{swc_id}"
                    current_finding.checks = self._map_mythril_to_checklist(swc_id)
                    current_finding.recommendation = self._get_mythril_recommendation(swc_id)
                elif line.startswith('Severity:'):
                    severity = line.replace('Severity:', '').strip()
                    current_finding.severity = self._normalize_severity(severity)
                else:
                    current_finding.description += f" {line}"
                    current_finding.tool_output += f"\n{line}"
        
        if current_finding:
            findings.append(current_finding)
            
        return findings

class AdapterRegistry:
    """Registry for managing analysis tool adapters."""
    
    def __init__(self, console: Console):
        self.console = console
        self._adapters: Dict[str, AnalyzerAdapter] = {}
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """Register default adapters."""
        self.register("slither", SlitherAdapter(self.console))
        self.register("mythril", MythrilAdapter(self.console))
    
    def register(self, name: str, adapter: AnalyzerAdapter):
        """Register an adapter."""
        self._adapters[name] = adapter
        self.console.print(f"[green]Registered adapter: {name}[/green]")
    
    def get(self, name: str) -> Optional[AnalyzerAdapter]:
        """Get an adapter by name."""
        return self._adapters.get(name)
    
    def list_available(self) -> List[str]:
        """List available adapters."""
        return list(self._adapters.keys())
    
    def health_check_all(self) -> Dict[str, bool]:
        """Run health checks on all adapters."""
        results = {}
        for name, adapter in self._adapters.items():
            try:
                results[name] = adapter.health_check()
            except Exception as e:
                self.console.print(f"[red]Health check failed for {name}: {e}[/red]")
                results[name] = False
        return results

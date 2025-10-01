"""Advanced Mythril integration module for Web3AuditMCP."""

import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.progress import Progress, TaskID

class MythrilModule:
    """Advanced Mythril symbolic execution integration."""
    
    def __init__(self, console: Console):
        self.console = console
        self.mythril_path = self._find_mythril()
        
    def _find_mythril(self) -> Optional[str]:
        """Find Mythril installation."""
        try:
            result = subprocess.run(['which', 'myth'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # Try common installation paths
        common_paths = [
            '/usr/local/bin/myth',
            '/usr/bin/myth',
            os.path.expanduser('~/.local/bin/myth')
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    def is_available(self) -> bool:
        """Check if Mythril is available."""
        return self.mythril_path is not None
    
    async def install_mythril(self) -> bool:
        """Install Mythril if not available."""
        if self.is_available():
            return True
            
        self.console.print("[yellow]Mythril not found. Installing...[/yellow]")
        
        try:
            # Install via pip
            result = subprocess.run([
                'pip', 'install', 'mythril'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.mythril_path = self._find_mythril()
                self.console.print("[green]✅ Mythril installed successfully[/green]")
                return True
            else:
                self.console.print(f"[red]Failed to install Mythril: {result.stderr}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error installing Mythril: {e}[/red]")
            return False
    
    def _prepare_solidity_file(self, target: str) -> Optional[str]:
        """Prepare Solidity file for Mythril analysis."""
        if target.endswith('.sol'):
            return target
        
        # If target is a directory, find .sol files
        if os.path.isdir(target):
            sol_files = list(Path(target).rglob('*.sol'))
            if sol_files:
                return str(sol_files[0])  # Return first .sol file found
        
        return None
    
    async def run_analysis(self, target: str, progress: Progress, task_id: TaskID) -> List[Dict[str, Any]]:
        """Run comprehensive Mythril symbolic execution."""
        findings = []
        
        if not self.is_available():
            if not await self.install_mythril():
                progress.update(task_id, description="[red]❌ Mythril unavailable")
                return findings
        
        try:
            progress.update(task_id, description="[yellow]🧠 Preparing Mythril analysis...")
            
            # Prepare Solidity file
            sol_file = self._prepare_solidity_file(target)
            if not sol_file:
                progress.update(task_id, description="[yellow]⚠️ No Solidity files found")
                return findings
            
            progress.update(task_id, description="[yellow]🧠 Running symbolic execution...")
            
            # Run Mythril analysis
            cmd = [
                self.mythril_path,
                'analyze',
                sol_file,
                '--output', 'json',
                '--execution-timeout', '300'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=400)
            
            if result.returncode == 0 and result.stdout:
                try:
                    mythril_output = json.loads(result.stdout)
                    findings = self._parse_mythril_output(mythril_output)
                    progress.update(task_id, description=f"[yellow]✅ Mythril found {len(findings)} issues")
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    findings = self._parse_text_output(result.stdout)
                    progress.update(task_id, description="[yellow]✅ Mythril analysis complete")
            else:
                progress.update(task_id, description="[yellow]⚠️ Mythril completed with warnings")
                if result.stdout:
                    findings = self._parse_text_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            progress.update(task_id, description="[red]⏰ Mythril analysis timed out")
        except Exception as e:
            progress.update(task_id, description=f"[red]❌ Mythril error: {str(e)[:30]}...")
            
        return findings
    
    def _parse_mythril_output(self, mythril_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Mythril JSON output into standardized findings."""
        findings = []
        
        # Mythril JSON structure varies, handle different formats
        if isinstance(mythril_output, dict):
            if 'issues' in mythril_output:
                issues = mythril_output['issues']
            elif 'success' in mythril_output and mythril_output.get('issues'):
                issues = mythril_output['issues']
            else:
                issues = [mythril_output] if mythril_output else []
        elif isinstance(mythril_output, list):
            issues = mythril_output
        else:
            return findings
        
        for issue in issues:
            if isinstance(issue, dict):
                finding = {
                    'tool': 'mythril',
                    'check': issue.get('swc-id', issue.get('title', 'unknown')),
                    'description': issue.get('description', issue.get('title', '')),
                    'impact': self._map_severity(issue.get('severity', 'Medium')),
                    'confidence': 'Medium',  # Mythril doesn't provide confidence
                    'elements': [],
                    'markdown': issue.get('description', ''),
                    'swc_id': issue.get('swc-id', ''),
                    'title': issue.get('title', ''),
                    'filename': issue.get('filename', ''),
                    'lineno': issue.get('lineno', 0),
                    'function': issue.get('function', ''),
                    'code': issue.get('code', ''),
                    'address': issue.get('address', 0),
                    'debug': issue.get('debug', '')
                }
                findings.append(finding)
        
        return findings
    
    def _map_severity(self, mythril_severity: str) -> str:
        """Map Mythril severity to standard format."""
        severity_map = {
            'High': 'High',
            'Medium': 'Medium', 
            'Low': 'Low',
            'Informational': 'Low'
        }
        return severity_map.get(mythril_severity, 'Medium')
    
    def _parse_text_output(self, text_output: str) -> List[Dict[str, Any]]:
        """Parse Mythril text output as fallback."""
        findings = []
        lines = text_output.split('\n')
        
        current_finding = None
        for line in lines:
            line = line.strip()
            
            # Detect issue start
            if line.startswith('==== ') and line.endswith(' ===='):
                if current_finding:
                    findings.append(current_finding)
                
                title = line.replace('====', '').strip()
                current_finding = {
                    'tool': 'mythril',
                    'check': title.lower().replace(' ', '-'),
                    'description': title,
                    'impact': 'Medium',
                    'confidence': 'Medium',
                    'elements': [],
                    'markdown': title,
                    'title': title
                }
            elif current_finding and line:
                # Add details to current finding
                if line.startswith('SWC ID:'):
                    current_finding['swc_id'] = line.replace('SWC ID:', '').strip()
                elif line.startswith('Severity:'):
                    severity = line.replace('Severity:', '').strip()
                    current_finding['impact'] = self._map_severity(severity)
                elif line.startswith('Contract:'):
                    current_finding['filename'] = line.replace('Contract:', '').strip()
                elif line.startswith('Function name:'):
                    current_finding['function'] = line.replace('Function name:', '').strip()
                else:
                    current_finding['description'] += f" {line}"
                    current_finding['markdown'] += f"\n{line}"
        
        if current_finding:
            findings.append(current_finding)
            
        return findings
    
    async def run_quick_analysis(self, target: str) -> List[Dict[str, Any]]:
        """Run quick Mythril analysis with reduced timeout."""
        if not self.is_available():
            return []
        
        sol_file = self._prepare_solidity_file(target)
        if not sol_file:
            return []
        
        try:
            cmd = [
                self.mythril_path,
                'analyze',
                sol_file,
                '--output', 'json',
                '--execution-timeout', '60'  # Quick analysis
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            
            if result.stdout:
                try:
                    mythril_output = json.loads(result.stdout)
                    return self._parse_mythril_output(mythril_output)
                except json.JSONDecodeError:
                    return self._parse_text_output(result.stdout)
                    
        except Exception:
            pass
            
        return []
    
    def get_supported_detectors(self) -> List[str]:
        """Get list of vulnerability types Mythril can detect."""
        return [
            'Integer Overflow',
            'Integer Underflow', 
            'Reentrancy',
            'Unchecked Call Return Value',
            'Unprotected Ether Withdrawal',
            'Unprotected Selfdestruct',
            'State Variable Default Visibility',
            'Deprecated Solidity Functions',
            'Delegatecall to Untrusted Contract',
            'Dependence on Predictable Environment Variable',
            'Weak Sources of Randomness',
            'Authorization through tx.origin',
            'Block values as a proxy for time',
            'Signature Malleability',
            'Incorrect Constructor Name',
            'Shadowing State Variables',
            'Weak Sources of Randomness from Chain Attributes',
            'Missing Constructor',
            'Uninitialized Storage Pointer',
            'Assert Violation',
            'Use of Deprecated Functions'
        ]

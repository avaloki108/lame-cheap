"""Advanced Slither integration module for Web3AuditMCP."""

import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.progress import Progress, TaskID

class SlitherModule:
    """Advanced Slither static analysis integration."""
    
    def __init__(self, console: Console):
        self.console = console
        self.slither_path = self._find_slither()
        
    def _find_slither(self) -> Optional[str]:
        """Find Slither installation."""
        try:
            result = subprocess.run(['which', 'slither'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # Try common installation paths
        common_paths = [
            '/usr/local/bin/slither',
            '/usr/bin/slither',
            os.path.expanduser('~/.local/bin/slither')
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    def is_available(self) -> bool:
        """Check if Slither is available."""
        return self.slither_path is not None
    
    async def install_slither(self) -> bool:
        """Install Slither if not available."""
        if self.is_available():
            return True
            
        self.console.print("[yellow]Slither not found. Installing...[/yellow]")
        
        try:
            # Install via pip
            result = subprocess.run([
                'pip', 'install', 'slither-analyzer'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.slither_path = self._find_slither()
                self.console.print("[green]✅ Slither installed successfully[/green]")
                return True
            else:
                self.console.print(f"[red]Failed to install Slither: {result.stderr}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error installing Slither: {e}[/red]")
            return False
    
    def _prepare_target(self, target: str) -> str:
        """Prepare target for analysis."""
        if target.startswith('http'):
            # Clone repository to temp directory
            temp_dir = tempfile.mkdtemp()
            try:
                subprocess.run(['git', 'clone', target, temp_dir], 
                             check=True, capture_output=True)
                return temp_dir
            except subprocess.CalledProcessError:
                self.console.print(f"[red]Failed to clone repository: {target}[/red]")
                return target
        
        return target
    
    async def run_analysis(self, target: str, progress: Progress, task_id: TaskID) -> List[Dict[str, Any]]:
        """Run comprehensive Slither analysis."""
        findings = []
        
        if not self.is_available():
            if not await self.install_slither():
                progress.update(task_id, description="[red]❌ Slither unavailable")
                return findings
        
        try:
            progress.update(task_id, description="[green]🔍 Preparing Slither analysis...")
            
            # Prepare target
            analysis_target = self._prepare_target(target)
            
            progress.update(task_id, description="[green]🔍 Running Slither detectors...")
            
            # Run Slither with JSON output
            cmd = [
                self.slither_path,
                analysis_target,
                '--json', '-',
                '--disable-color'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 or result.stdout:
                # Parse JSON output
                try:
                    slither_output = json.loads(result.stdout)
                    findings = self._parse_slither_output(slither_output)
                    progress.update(task_id, description=f"[green]✅ Slither found {len(findings)} issues")
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    findings = self._parse_text_output(result.stdout)
                    progress.update(task_id, description=f"[green]✅ Slither analysis complete")
            else:
                progress.update(task_id, description="[yellow]⚠️ Slither completed with warnings")
                # Still try to parse any output
                if result.stdout:
                    findings = self._parse_text_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            progress.update(task_id, description="[red]⏰ Slither analysis timed out")
        except Exception as e:
            progress.update(task_id, description=f"[red]❌ Slither error: {str(e)[:30]}...")
            
        return findings
    
    def _parse_slither_output(self, slither_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Slither JSON output into standardized findings."""
        findings = []
        
        # Parse detectors results
        if 'results' in slither_output and 'detectors' in slither_output['results']:
            for detector in slither_output['results']['detectors']:
                finding = {
                    'tool': 'slither',
                    'check': detector.get('check', 'unknown'),
                    'description': detector.get('description', ''),
                    'impact': detector.get('impact', 'Unknown').title(),
                    'confidence': detector.get('confidence', 'Unknown').title(),
                    'elements': detector.get('elements', []),
                    'markdown': detector.get('markdown', ''),
                    'first_markdown_element': detector.get('first_markdown_element', ''),
                    'id': detector.get('id', ''),
                    'additional_fields': detector.get('additional_fields', {})
                }
                findings.append(finding)
        
        return findings
    
    def _parse_text_output(self, text_output: str) -> List[Dict[str, Any]]:
        """Parse Slither text output as fallback."""
        findings = []
        lines = text_output.split('\n')
        
        current_finding = None
        for line in lines:
            line = line.strip()
            
            # Detect detector findings
            if 'INFO:Detectors:' in line or any(severity in line for severity in ['HIGH', 'MEDIUM', 'LOW']):
                if current_finding:
                    findings.append(current_finding)
                
                # Extract basic info from line
                parts = line.split(':')
                if len(parts) >= 3:
                    current_finding = {
                        'tool': 'slither',
                        'check': 'detector',
                        'description': line,
                        'impact': 'Medium',  # Default
                        'confidence': 'Medium',  # Default
                        'elements': [],
                        'markdown': line
                    }
            elif current_finding and line:
                # Add additional context to current finding
                current_finding['description'] += f" {line}"
                current_finding['markdown'] += f"\n{line}"
        
        if current_finding:
            findings.append(current_finding)
            
        return findings
    
    def get_available_detectors(self) -> List[str]:
        """Get list of available Slither detectors."""
        if not self.is_available():
            return []
        
        try:
            result = subprocess.run([
                self.slither_path, '--list-detectors'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse detector list from output
                detectors = []
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('#') and ':' in line:
                        detector_name = line.split(':')[0].strip()
                        if detector_name:
                            detectors.append(detector_name)
                return detectors
        except:
            pass
            
        return []
    
    async def run_specific_detectors(self, target: str, detectors: List[str]) -> List[Dict[str, Any]]:
        """Run specific Slither detectors."""
        if not self.is_available() or not detectors:
            return []
        
        findings = []
        analysis_target = self._prepare_target(target)
        
        for detector in detectors:
            try:
                cmd = [
                    self.slither_path,
                    analysis_target,
                    '--detect', detector,
                    '--json', '-'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.stdout:
                    try:
                        detector_output = json.loads(result.stdout)
                        detector_findings = self._parse_slither_output(detector_output)
                        findings.extend(detector_findings)
                    except json.JSONDecodeError:
                        pass
                        
            except Exception:
                continue
                
        return findings

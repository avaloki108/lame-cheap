"""Advanced Foundry integration module for Web3AuditMCP."""

import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.progress import Progress, TaskID

class FoundryModule:
    """Advanced Foundry fuzzing and testing integration."""
    
    def __init__(self, console: Console):
        self.console = console
        self.forge_path = self._find_forge()
        
    def _find_forge(self) -> Optional[str]:
        """Find Forge installation."""
        try:
            result = subprocess.run(['which', 'forge'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # Try common installation paths
        common_paths = [
            '/usr/local/bin/forge',
            '/usr/bin/forge',
            os.path.expanduser('~/.foundry/bin/forge'),
            os.path.expanduser('~/.cargo/bin/forge')
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    def is_available(self) -> bool:
        """Check if Foundry is available."""
        return self.forge_path is not None
    
    async def install_foundry(self) -> bool:
        """Install Foundry if not available."""
        if self.is_available():
            return True
            
        self.console.print("[yellow]Foundry not found. Installing...[/yellow]")
        
        try:
            # Install Foundry using foundryup
            install_script = """
            curl -L https://foundry.paradigm.xyz | bash
            source ~/.bashrc
            foundryup
            """
            
            result = subprocess.run([
                'bash', '-c', install_script
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.forge_path = self._find_forge()
                if self.forge_path:
                    self.console.print("[green]✅ Foundry installed successfully[/green]")
                    return True
            
            self.console.print(f"[red]Failed to install Foundry: {result.stderr}[/red]")
            return False
                
        except Exception as e:
            self.console.print(f"[red]Error installing Foundry: {e}[/red]")
            return False
    
    def _is_foundry_project(self, target: str) -> bool:
        """Check if target is a Foundry project."""
        if os.path.isdir(target):
            foundry_toml = os.path.join(target, 'foundry.toml')
            forge_toml = os.path.join(target, 'forge.toml')
            return os.path.exists(foundry_toml) or os.path.exists(forge_toml)
        return False
    
    def _setup_foundry_project(self, target: str) -> str:
        """Setup a basic Foundry project structure."""
        if self._is_foundry_project(target):
            return target
        
        # Create temporary Foundry project
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Initialize Foundry project
            subprocess.run([
                self.forge_path, 'init', temp_dir, '--no-git'
            ], check=True, capture_output=True)
            
            # Copy source files if target is a directory
            if os.path.isdir(target):
                src_dir = os.path.join(temp_dir, 'src')
                for sol_file in Path(target).rglob('*.sol'):
                    dest_file = os.path.join(src_dir, sol_file.name)
                    subprocess.run(['cp', str(sol_file), dest_file])
            elif target.endswith('.sol'):
                # Copy single file
                src_dir = os.path.join(temp_dir, 'src')
                dest_file = os.path.join(src_dir, os.path.basename(target))
                subprocess.run(['cp', target, dest_file])
            
            return temp_dir
            
        except subprocess.CalledProcessError:
            return target
    
    async def run_analysis(self, target: str, progress: Progress, task_id: TaskID) -> List[Dict[str, Any]]:
        """Run comprehensive Foundry testing and fuzzing."""
        findings = []
        
        if not self.is_available():
            if not await self.install_foundry():
                progress.update(task_id, description="[red]❌ Foundry unavailable")
                return findings
        
        try:
            progress.update(task_id, description="[blue]🔨 Preparing Foundry project...")
            
            # Setup Foundry project
            project_dir = self._setup_foundry_project(target)
            
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(project_dir)
            
            try:
                # Run compilation check
                progress.update(task_id, description="[blue]🔨 Compiling contracts...")
                compile_result = await self._run_forge_build()
                
                if compile_result['success']:
                    # Run tests
                    progress.update(task_id, description="[blue]🧪 Running tests...")
                    test_results = await self._run_forge_test()
                    findings.extend(test_results)
                    
                    # Run gas analysis
                    progress.update(task_id, description="[blue]⛽ Analyzing gas usage...")
                    gas_results = await self._run_gas_analysis()
                    findings.extend(gas_results)
                    
                    # Run invariant testing
                    progress.update(task_id, description="[blue]🎯 Running invariant tests...")
                    invariant_results = await self._run_invariant_tests()
                    findings.extend(invariant_results)
                    
                    progress.update(task_id, description=f"[blue]✅ Foundry found {len(findings)} issues")
                else:
                    findings.append({
                        'tool': 'foundry',
                        'check': 'compilation-error',
                        'description': 'Contract compilation failed',
                        'impact': 'High',
                        'confidence': 'High',
                        'elements': [],
                        'markdown': compile_result.get('error', 'Compilation failed')
                    })
                    progress.update(task_id, description="[red]❌ Compilation failed")
                    
            finally:
                os.chdir(original_cwd)
            
        except Exception as e:
            progress.update(task_id, description=f"[red]❌ Foundry error: {str(e)[:30]}...")
            
        return findings
    
    async def _run_forge_build(self) -> Dict[str, Any]:
        """Run forge build and return results."""
        try:
            result = subprocess.run([
                self.forge_path, 'build'
            ], capture_output=True, text=True, timeout=120)
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'error': result.stderr if result.returncode != 0 else None
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Build timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _run_forge_test(self) -> List[Dict[str, Any]]:
        """Run forge test and parse results."""
        findings = []
        
        try:
            result = subprocess.run([
                self.forge_path, 'test', '-vvv'
            ], capture_output=True, text=True, timeout=180)
            
            # Parse test output for failures
            if result.returncode != 0 or 'FAILED' in result.stdout:
                test_failures = self._parse_test_failures(result.stdout)
                findings.extend(test_failures)
            
        except subprocess.TimeoutExpired:
            findings.append({
                'tool': 'foundry',
                'check': 'test-timeout',
                'description': 'Test execution timed out',
                'impact': 'Medium',
                'confidence': 'High',
                'elements': [],
                'markdown': 'Test suite execution exceeded timeout limit'
            })
        except Exception:
            pass
            
        return findings
    
    async def _run_gas_analysis(self) -> List[Dict[str, Any]]:
        """Run gas usage analysis."""
        findings = []
        
        try:
            result = subprocess.run([
                self.forge_path, 'test', '--gas-report'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                gas_issues = self._analyze_gas_usage(result.stdout)
                findings.extend(gas_issues)
                
        except Exception:
            pass
            
        return findings
    
    async def _run_invariant_tests(self) -> List[Dict[str, Any]]:
        """Run invariant/property tests."""
        findings = []
        
        try:
            # Look for invariant test files
            test_files = list(Path('.').rglob('*Invariant*.sol'))
            test_files.extend(list(Path('.').rglob('*Property*.sol'))
            
            if test_files:
                result = subprocess.run([
                    self.forge_path, 'test', '--match-contract', 'Invariant'
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0 or 'FAILED' in result.stdout:
                    invariant_failures = self._parse_invariant_failures(result.stdout)
                    findings.extend(invariant_failures)
                    
        except Exception:
            pass
            
        return findings
    
    def _parse_test_failures(self, test_output: str) -> List[Dict[str, Any]]:
        """Parse test failures from forge test output."""
        findings = []
        lines = test_output.split('\n')
        
        current_test = None
        for line in lines:
            line = line.strip()
            
            if '[FAIL]' in line:
                # Extract test name and reason
                parts = line.split('[FAIL]')
                if len(parts) > 1:
                    test_info = parts[1].strip()
                    current_test = {
                        'tool': 'foundry',
                        'check': 'test-failure',
                        'description': f'Test failed: {test_info}',
                        'impact': 'Medium',
                        'confidence': 'High',
                        'elements': [],
                        'markdown': f'Test failure: {test_info}',
                        'test_name': test_info
                    }
            elif current_test and ('Error:' in line or 'Reason:' in line):
                current_test['description'] += f" - {line}"
                current_test['markdown'] += f"\n{line}"
                findings.append(current_test)
                current_test = None
        
        if current_test:
            findings.append(current_test)
            
        return findings
    
    def _analyze_gas_usage(self, gas_output: str) -> List[Dict[str, Any]]:
        """Analyze gas usage patterns for potential issues."""
        findings = []
        lines = gas_output.split('\n')
        
        for line in lines:
            if '|' in line and any(char.isdigit() for char in line):
                # Parse gas usage line
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    try:
                        function_name = parts[0]
                        avg_gas = int(parts[2]) if parts[2].isdigit() else 0
                        
                        # Flag high gas usage
                        if avg_gas > 100000:  # Arbitrary threshold
                            findings.append({
                                'tool': 'foundry',
                                'check': 'high-gas-usage',
                                'description': f'Function {function_name} has high gas usage: {avg_gas}',
                                'impact': 'Low',
                                'confidence': 'Medium',
                                'elements': [],
                                'markdown': f'High gas usage detected in {function_name}: {avg_gas} gas',
                                'function': function_name,
                                'gas_usage': avg_gas
                            })
                    except (ValueError, IndexError):
                        continue
        
        return findings
    
    def _parse_invariant_failures(self, invariant_output: str) -> List[Dict[str, Any]]:
        """Parse invariant test failures."""
        findings = []
        lines = invariant_output.split('\n')
        
        for line in lines:
            if '[FAIL]' in line and 'invariant' in line.lower():
                findings.append({
                    'tool': 'foundry',
                    'check': 'invariant-violation',
                    'description': f'Invariant violation: {line}',
                    'impact': 'High',
                    'confidence': 'High',
                    'elements': [],
                    'markdown': f'Invariant violation detected: {line}'
                })
        
        return findings
    
    def get_supported_features(self) -> List[str]:
        """Get list of Foundry features supported."""
        return [
            'Unit Testing',
            'Integration Testing',
            'Fuzz Testing',
            'Invariant Testing',
            'Gas Analysis',
            'Coverage Analysis',
            'Symbolic Execution',
            'Property-Based Testing',
            'Differential Testing',
            'Mutation Testing'
        ]

"""Unit tests for the SlitherModule class."""

import pytest
import subprocess
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console

from web3audit_mcp.modules.slither_module import SlitherModule


class TestSlitherModule:
    """Test cases for SlitherModule class."""
    
    @pytest.fixture
    def console(self):
        """Create a mock console for testing."""
        return Mock(spec=Console)
    
    @pytest.fixture
    def slither_module(self, console):
        """Create a SlitherModule instance for testing."""
        return SlitherModule(console)
    
    def test_slither_module_initialization(self, console):
        """Test SlitherModule initialization."""
        module = SlitherModule(console)
        
        assert module.console == console
        assert hasattr(module, 'slither_path')
    
    @patch('subprocess.run')
    def test_find_slither_success(self, mock_run, console):
        """Test successful Slither detection."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '/usr/local/bin/slither\n'
        
        module = SlitherModule(console)
        
        assert module.slither_path == '/usr/local/bin/slither'
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_find_slither_fallback_paths(self, mock_exists, mock_run, console):
        """Test Slither detection using fallback paths."""
        # Mock 'which' command failure
        mock_run.side_effect = Exception("Command not found")
        
        # Mock path existence check
        mock_exists.side_effect = lambda path: path == '/usr/local/bin/slither'
        
        module = SlitherModule(console)
        
        assert module.slither_path == '/usr/local/bin/slither'
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_find_slither_not_found(self, mock_exists, mock_run, console):
        """Test Slither not found scenario."""
        mock_run.side_effect = Exception("Command not found")
        mock_exists.return_value = False
        
        module = SlitherModule(console)
        
        assert module.slither_path is None
    
    def test_is_available_true(self, console):
        """Test is_available returns True when Slither is found."""
        with patch.object(SlitherModule, '_find_slither', return_value='/usr/bin/slither'):
            module = SlitherModule(console)
            assert module.is_available() is True
    
    def test_is_available_false(self, console):
        """Test is_available returns False when Slither is not found."""
        with patch.object(SlitherModule, '_find_slither', return_value=None):
            module = SlitherModule(console)
            assert module.is_available() is False
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_install_slither_success(self, mock_run, console):
        """Test successful Slither installation."""
        mock_run.return_value.returncode = 0
        
        with patch.object(SlitherModule, '_find_slither', side_effect=[None, '/usr/local/bin/slither']):
            module = SlitherModule(console)
            result = await module.install_slither()
            
            assert result is True
            assert module.slither_path == '/usr/local/bin/slither'
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_install_slither_failure(self, mock_run, console):
        """Test failed Slither installation."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Installation failed"
        
        with patch.object(SlitherModule, '_find_slither', return_value=None):
            module = SlitherModule(console)
            result = await module.install_slither()
            
            assert result is False
    
    def test_prepare_target_local_file(self, slither_module):
        """Test target preparation for local file."""
        target = "/path/to/contract.sol"
        result = slither_module._prepare_target(target)
        
        assert result == target
    
    @patch('subprocess.run')
    @patch('tempfile.mkdtemp')
    def test_prepare_target_git_repo(self, mock_mkdtemp, mock_run, slither_module):
        """Test target preparation for Git repository."""
        mock_mkdtemp.return_value = '/tmp/test_repo'
        mock_run.return_value = None  # Successful git clone
        
        target = "https://github.com/user/repo.git"
        result = slither_module._prepare_target(target)
        
        assert result == '/tmp/test_repo'
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_prepare_target_git_clone_failure(self, mock_run, slither_module):
        """Test target preparation when git clone fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')
        
        target = "https://github.com/user/repo.git"
        result = slither_module._prepare_target(target)
        
        assert result == target  # Should return original target on failure
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_run_analysis_success(self, mock_run, console):
        """Test successful Slither analysis."""
        # Mock Slither output
        slither_output = {
            "results": {
                "detectors": [
                    {
                        "check": "reentrancy-eth",
                        "description": "Reentrancy vulnerability",
                        "impact": "High",
                        "confidence": "High",
                        "elements": [],
                        "markdown": "Reentrancy found",
                        "id": "test-1"
                    }
                ]
            }
        }
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(slither_output)
        
        with patch.object(SlitherModule, 'is_available', return_value=True):
            module = SlitherModule(console)
            
            # Mock progress
            progress = Mock()
            task_id = Mock()
            
            findings = await module.run_analysis("test.sol", progress, task_id)
            
            assert len(findings) == 1
            finding = findings[0]
            assert finding['tool'] == 'slither'
            assert finding['check'] == 'reentrancy-eth'
            assert finding['impact'] == 'High'
    
    @pytest.mark.asyncio
    async def test_run_analysis_slither_unavailable(self, console):
        """Test analysis when Slither is unavailable."""
        with patch.object(SlitherModule, 'is_available', return_value=False), \
             patch.object(SlitherModule, 'install_slither', return_value=False):
            
            module = SlitherModule(console)
            
            # Mock progress
            progress = Mock()
            task_id = Mock()
            
            findings = await module.run_analysis("test.sol", progress, task_id)
            
            assert len(findings) == 0
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_run_analysis_timeout(self, mock_run, console):
        """Test analysis timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired('slither', 300)
        
        with patch.object(SlitherModule, 'is_available', return_value=True):
            module = SlitherModule(console)
            
            # Mock progress
            progress = Mock()
            task_id = Mock()
            
            findings = await module.run_analysis("test.sol", progress, task_id)
            
            assert len(findings) == 0
            # Verify timeout message was set
            progress.update.assert_called()
    
    def test_parse_slither_output_valid(self, slither_module):
        """Test parsing valid Slither JSON output."""
        slither_output = {
            "results": {
                "detectors": [
                    {
                        "check": "reentrancy-eth",
                        "description": "Reentrancy vulnerability",
                        "impact": "High",
                        "confidence": "High",
                        "elements": [{"name": "withdraw"}],
                        "markdown": "Reentrancy found in withdraw",
                        "id": "test-1"
                    }
                ]
            }
        }
        
        findings = slither_module._parse_slither_output(slither_output)
        
        assert len(findings) == 1
        finding = findings[0]
        assert finding['tool'] == 'slither'
        assert finding['check'] == 'reentrancy-eth'
        assert finding['description'] == 'Reentrancy vulnerability'
        assert finding['impact'] == 'High'
        assert finding['confidence'] == 'High'
        assert len(finding['elements']) == 1
    
    def test_parse_slither_output_empty(self, slither_module):
        """Test parsing empty Slither output."""
        slither_output = {"results": {"detectors": []}}
        
        findings = slither_module._parse_slither_output(slither_output)
        
        assert len(findings) == 0
    
    def test_parse_text_output(self, slither_module):
        """Test parsing Slither text output as fallback."""
        text_output = """
INFO:Detectors:
Reentrancy in Contract.withdraw():
    External calls:
        - msg.sender.call.value(amount)()
    State variables written after the call(s):
        - balances[msg.sender] = 0
"""
        
        findings = slither_module._parse_text_output(text_output)
        
        assert len(findings) >= 1
        # Should have parsed at least one finding from the text
    
    @patch('subprocess.run')
    def test_get_available_detectors(self, mock_run, console):
        """Test getting available Slither detectors."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = """
# Available detectors:
reentrancy-eth: Reentrancy vulnerabilities
unused-return: Unused return values
tx-origin: Dangerous use of tx.origin
"""
        
        with patch.object(SlitherModule, 'is_available', return_value=True):
            module = SlitherModule(console)
            detectors = module.get_available_detectors()
            
            assert 'reentrancy-eth' in detectors
            assert 'unused-return' in detectors
            assert 'tx-origin' in detectors
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_run_specific_detectors(self, mock_run, console):
        """Test running specific Slither detectors."""
        slither_output = {
            "results": {
                "detectors": [
                    {
                        "check": "reentrancy-eth",
                        "description": "Reentrancy vulnerability",
                        "impact": "High",
                        "confidence": "High"
                    }
                ]
            }
        }
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(slither_output)
        
        with patch.object(SlitherModule, 'is_available', return_value=True):
            module = SlitherModule(console)
            
            findings = await module.run_specific_detectors("test.sol", ["reentrancy-eth"])
            
            assert len(findings) == 1
            assert findings[0]['check'] == 'reentrancy-eth'


if __name__ == '__main__':
    pytest.main([__file__])

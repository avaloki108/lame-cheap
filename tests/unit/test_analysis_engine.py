"""Unit tests for the AnalysisEngine class."""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from rich.console import Console

from web3audit_mcp.analysis_engine import AnalysisEngine, VulnerabilityCheck


class TestVulnerabilityCheck:
    """Test cases for VulnerabilityCheck class."""
    
    def test_vulnerability_check_initialization(self):
        """Test VulnerabilityCheck initialization with valid data."""
        check_data = {
            "id": "test-001",
            "question": "Is the contract vulnerable to reentrancy?",
            "description": "Check for reentrancy vulnerabilities",
            "remediation": "Use reentrancy guards",
            "references": ["https://example.com"],
            "tags": ["reentrancy", "security"],
            "category": "Reentrancy"
        }
        
        check = VulnerabilityCheck(check_data)
        
        assert check.id == "test-001"
        assert check.question == "Is the contract vulnerable to reentrancy?"
        assert check.description == "Check for reentrancy vulnerabilities"
        assert check.remediation == "Use reentrancy guards"
        assert check.references == ["https://example.com"]
        assert check.tags == ["reentrancy", "security"]
        assert check.category == "Reentrancy"
    
    def test_vulnerability_check_with_missing_fields(self):
        """Test VulnerabilityCheck with missing optional fields."""
        check_data = {"id": "test-002"}
        
        check = VulnerabilityCheck(check_data)
        
        assert check.id == "test-002"
        assert check.question == ""
        assert check.description == ""
        assert check.remediation == ""
        assert check.references == []
        assert check.tags == []
        assert check.category == ""


class TestAnalysisEngine:
    """Test cases for AnalysisEngine class."""
    
    @pytest.fixture
    def console(self):
        """Create a mock console for testing."""
        return Mock(spec=Console)
    
    @pytest.fixture
    def sample_checklist_data(self):
        """Create sample checklist data for testing."""
        return [
            {
                "category": "Reentrancy",
                "data": [
                    {
                        "category": "Cross-function Reentrancy",
                        "data": [
                            {
                                "id": "reentrancy-001",
                                "question": "Can the contract be reentered?",
                                "description": "Check for reentrancy vulnerabilities",
                                "remediation": "Use reentrancy guards",
                                "references": [],
                                "tags": ["reentrancy"]
                            }
                        ]
                    }
                ]
            }
        ]
    
    @pytest.fixture
    def temp_checklist_file(self, sample_checklist_data):
        """Create a temporary checklist file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_checklist_data, f)
            return f.name
    
    def test_analysis_engine_initialization(self, console):
        """Test AnalysisEngine initialization."""
        engine = AnalysisEngine(console)
        
        assert engine.console == console
        assert hasattr(engine, 'slither_module')
        assert hasattr(engine, 'mythril_module')
        assert hasattr(engine, 'foundry_module')
        assert isinstance(engine.vulnerability_checks, list)
    
    def test_load_vulnerability_checklist_success(self, console, temp_checklist_file):
        """Test successful loading of vulnerability checklist."""
        engine = AnalysisEngine(console, temp_checklist_file)
        
        assert len(engine.vulnerability_checks) == 1
        check = engine.vulnerability_checks[0]
        assert check.id == "reentrancy-001"
        assert check.category == "Cross-function Reentrancy"
    
    def test_load_vulnerability_checklist_file_not_found(self, console):
        """Test handling of missing checklist file."""
        engine = AnalysisEngine(console, "nonexistent_file.json")
        
        # Should handle gracefully and have empty checklist
        assert len(engine.vulnerability_checks) == 0
    
    @pytest.mark.asyncio
    async def test_check_donation_attacks(self, console):
        """Test donation attack vulnerability checking."""
        engine = AnalysisEngine(console)
        
        findings = await engine._check_donation_attacks("test_contract.sol")
        
        assert len(findings) == 1
        finding = findings[0]
        assert finding['tool'] == 'custom'
        assert finding['check'] == 'donation-attack'
        assert finding['impact'] == 'High'
        assert 'donation attacks' in finding['description']
    
    @pytest.mark.asyncio
    async def test_check_frontrunning(self, console):
        """Test front-running vulnerability checking."""
        engine = AnalysisEngine(console)
        
        findings = await engine._check_frontrunning("test_contract.sol")
        
        assert len(findings) == 1
        finding = findings[0]
        assert finding['tool'] == 'custom'
        assert finding['check'] == 'front-running'
        assert finding['impact'] == 'Medium'
        assert 'front-running' in finding['description']
    
    @pytest.mark.asyncio
    async def test_check_reentrancy_patterns(self, console):
        """Test reentrancy pattern checking."""
        engine = AnalysisEngine(console)
        
        findings = await engine._check_reentrancy_patterns("test_contract.sol")
        
        assert len(findings) == 1
        finding = findings[0]
        assert finding['tool'] == 'custom'
        assert finding['check'] == 'cross-function-reentrancy'
        assert finding['impact'] == 'High'
        assert 'reentrancy' in finding['description']
    
    @pytest.mark.asyncio
    async def test_check_access_control(self, console):
        """Test access control vulnerability checking."""
        engine = AnalysisEngine(console)
        
        findings = await engine._check_access_control("test_contract.sol")
        
        assert len(findings) == 1
        finding = findings[0]
        assert finding['tool'] == 'custom'
        assert finding['check'] == 'missing-access-control'
        assert finding['impact'] == 'High'
        assert 'access control' in finding['description']
    
    @pytest.mark.asyncio
    async def test_run_custom_checks(self, console):
        """Test running all custom vulnerability checks."""
        engine = AnalysisEngine(console)
        
        # Mock progress
        progress = Mock()
        task_id = Mock()
        
        findings = await engine.run_custom_checks("test_contract.sol", progress, task_id)
        
        # Should have findings from all custom check methods
        assert len(findings) >= 4  # donation, frontrun, reentrancy, access control
        
        # Verify progress updates were called
        assert progress.update.called
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self, console):
        """Test comprehensive analysis orchestration."""
        engine = AnalysisEngine(console)
        
        # Mock the individual analysis methods
        with patch.object(engine, 'run_slither_analysis', new_callable=AsyncMock) as mock_slither, \
             patch.object(engine, 'run_mythril_analysis', new_callable=AsyncMock) as mock_mythril, \
             patch.object(engine, 'run_foundry_analysis', new_callable=AsyncMock) as mock_foundry, \
             patch.object(engine, 'run_custom_checks', new_callable=AsyncMock) as mock_custom:
            
            # Setup mock returns
            mock_slither.return_value = [{'tool': 'slither', 'impact': 'High'}]
            mock_mythril.return_value = [{'tool': 'mythril', 'impact': 'Medium'}]
            mock_foundry.return_value = [{'tool': 'foundry', 'impact': 'Low'}]
            mock_custom.return_value = [{'tool': 'custom', 'impact': 'High'}]
            
            results = await engine.comprehensive_analysis("test_contract.sol")
            
            # Verify all analysis methods were called
            mock_slither.assert_called_once()
            mock_mythril.assert_called_once()
            mock_foundry.assert_called_once()
            mock_custom.assert_called_once()
            
            # Verify results structure
            assert results['target'] == "test_contract.sol"
            assert results['total_findings'] == 4
            assert results['high_severity'] == 2
            assert results['medium_severity'] == 1
            assert results['low_severity'] == 1
            assert results['risk_score'] == 26  # 2*10 + 1*5 + 1*1
            assert 'tool_status' in results
    
    def test_generate_detailed_report(self, console):
        """Test detailed report generation."""
        engine = AnalysisEngine(console)
        
        analysis_results = {
            'target': 'test_contract.sol',
            'total_findings': 5,
            'high_severity': 2,
            'medium_severity': 2,
            'low_severity': 1,
            'risk_score': 27,
            'findings': [
                {
                    'tool': 'slither',
                    'check': 'reentrancy-eth',
                    'description': 'Reentrancy vulnerability found',
                    'impact': 'High'
                },
                {
                    'tool': 'mythril',
                    'check': 'integer-overflow',
                    'description': 'Integer overflow detected',
                    'impact': 'Medium'
                }
            ],
            'tool_status': {
                'slither': True,
                'mythril': False,
                'foundry': True
            }
        }
        
        report_panel = engine.generate_detailed_report(analysis_results)
        
        # Verify panel was created
        assert report_panel is not None
        assert hasattr(report_panel, 'renderable')
    
    def test_get_tool_availability(self, console):
        """Test tool availability checking."""
        engine = AnalysisEngine(console)
        
        # Mock module availability
        with patch.object(engine.slither_module, 'is_available', return_value=True), \
             patch.object(engine.mythril_module, 'is_available', return_value=False), \
             patch.object(engine.foundry_module, 'is_available', return_value=True):
            
            availability = engine.get_tool_availability()
            
            assert availability['slither'] is True
            assert availability['mythril'] is False
            assert availability['foundry'] is True
            assert availability['custom_checks'] is True  # Should be True if checklist loaded


if __name__ == '__main__':
    pytest.main([__file__])

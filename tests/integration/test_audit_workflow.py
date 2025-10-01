"""Integration tests for the complete audit workflow."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from rich.console import Console

from web3audit_mcp.orchestration import OrchestrationLayer
from web3audit_mcp.analysis_engine import AnalysisEngine
from web3audit_mcp.client import Web3AuditClient


class TestAuditWorkflow:
    """Integration tests for the complete audit workflow."""
    
    @pytest.fixture
    def console(self):
        """Create a console for testing."""
        return Console()
    
    @pytest.fixture
    def sample_solidity_contract(self):
        """Create a sample Solidity contract for testing."""
        contract_code = '''
pragma solidity ^0.8.0;

contract VulnerableContract {
    mapping(address => uint256) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // Vulnerable to reentrancy
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount;
    }
    
    function getBalance() public view returns (uint256) {
        return address(this).balance;  // Vulnerable to donation attacks
    }
}
'''
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
            f.write(contract_code)
            return f.name
    
    @pytest.fixture
    def sample_foundry_project(self, sample_solidity_contract):
        """Create a sample Foundry project structure."""
        temp_dir = tempfile.mkdtemp()
        
        # Create basic Foundry structure
        src_dir = os.path.join(temp_dir, 'src')
        test_dir = os.path.join(temp_dir, 'test')
        os.makedirs(src_dir)
        os.makedirs(test_dir)
        
        # Copy contract to src directory
        contract_dest = os.path.join(src_dir, 'VulnerableContract.sol')
        with open(sample_solidity_contract, 'r') as src, open(contract_dest, 'w') as dst:
            dst.write(src.read())
        
        # Create foundry.toml
        foundry_toml = os.path.join(temp_dir, 'foundry.toml')
        with open(foundry_toml, 'w') as f:
            f.write('''
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
''')
        
        # Create basic test
        test_file = os.path.join(test_dir, 'VulnerableContract.t.sol')
        with open(test_file, 'w') as f:
            f.write('''
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/VulnerableContract.sol";

contract VulnerableContractTest is Test {
    VulnerableContract public vulnerableContract;
    
    function setUp() public {
        vulnerableContract = new VulnerableContract();
    }
    
    function testDeposit() public {
        vulnerableContract.deposit{value: 1 ether}();
        assertEq(vulnerableContract.balances(address(this)), 1 ether);
    }
}
''')
        
        return temp_dir
    
    @pytest.mark.asyncio
    async def test_orchestration_layer_start_audit(self, console, sample_solidity_contract):
        """Test the orchestration layer audit workflow."""
        orchestration = OrchestrationLayer(console)
        
        # Mock the analysis engine methods to avoid actual tool execution
        with patch.object(orchestration.analysis_engine, 'comprehensive_analysis') as mock_analysis:
            mock_analysis.return_value = {
                'target': sample_solidity_contract,
                'total_findings': 3,
                'high_severity': 2,
                'medium_severity': 1,
                'low_severity': 0,
                'risk_score': 25,
                'findings': [
                    {
                        'tool': 'slither',
                        'check': 'reentrancy-eth',
                        'description': 'Reentrancy vulnerability in withdraw function',
                        'impact': 'High',
                        'confidence': 'High'
                    },
                    {
                        'tool': 'custom',
                        'check': 'donation-attack',
                        'description': 'Contract vulnerable to donation attacks',
                        'impact': 'High',
                        'confidence': 'Medium'
                    },
                    {
                        'tool': 'mythril',
                        'check': 'unchecked-send',
                        'description': 'Unchecked external call return value',
                        'impact': 'Medium',
                        'confidence': 'High'
                    }
                ],
                'high_findings': [],
                'medium_findings': [],
                'low_findings': [],
                'tool_status': {
                    'slither': True,
                    'mythril': True,
                    'foundry': True
                }
            }
            
            config = {'target': sample_solidity_contract}
            report_panel = await orchestration.start_audit(config)
            
            # Verify analysis was called
            mock_analysis.assert_called_once_with(sample_solidity_contract)
            
            # Verify report panel was generated
            assert report_panel is not None
            assert hasattr(report_panel, 'renderable')
    
    @pytest.mark.asyncio
    async def test_orchestration_layer_quick_scan(self, console, sample_solidity_contract):
        """Test the orchestration layer quick scan workflow."""
        orchestration = OrchestrationLayer(console)
        
        report_panel = await orchestration.quick_scan(sample_solidity_contract)
        
        # Verify report panel was generated
        assert report_panel is not None
        assert hasattr(report_panel, 'renderable')
    
    @pytest.mark.asyncio
    async def test_analysis_engine_comprehensive_workflow(self, console, sample_solidity_contract):
        """Test the analysis engine comprehensive analysis workflow."""
        engine = AnalysisEngine(console)
        
        # Mock individual analysis modules to avoid actual tool execution
        with patch.object(engine.slither_module, 'run_analysis') as mock_slither, \
             patch.object(engine.mythril_module, 'run_analysis') as mock_mythril, \
             patch.object(engine.foundry_module, 'run_analysis') as mock_foundry:
            
            # Setup mock returns
            mock_slither.return_value = [
                {
                    'tool': 'slither',
                    'check': 'reentrancy-eth',
                    'description': 'Reentrancy vulnerability detected',
                    'impact': 'High',
                    'confidence': 'High'
                }
            ]
            
            mock_mythril.return_value = [
                {
                    'tool': 'mythril',
                    'check': 'integer-overflow',
                    'description': 'Integer overflow vulnerability',
                    'impact': 'Medium',
                    'confidence': 'Medium'
                }
            ]
            
            mock_foundry.return_value = [
                {
                    'tool': 'foundry',
                    'check': 'test-failure',
                    'description': 'Test case failed',
                    'impact': 'Low',
                    'confidence': 'High'
                }
            ]
            
            results = await engine.comprehensive_analysis(sample_solidity_contract)
            
            # Verify all modules were called
            mock_slither.assert_called_once()
            mock_mythril.assert_called_once()
            mock_foundry.assert_called_once()
            
            # Verify results structure
            assert results['target'] == sample_solidity_contract
            assert results['total_findings'] >= 4  # 3 from modules + custom checks
            assert results['high_severity'] >= 1
            assert results['medium_severity'] >= 1
            assert results['low_severity'] >= 1
            assert 'risk_score' in results
            assert 'tool_status' in results
    
    @pytest.mark.asyncio
    async def test_client_audit_command_workflow(self, console, sample_solidity_contract):
        """Test the client audit command workflow."""
        # Mock Ollama client
        mock_ollama = Mock()
        
        client = Web3AuditClient()
        client.ollama = mock_ollama
        client.console = console
        
        # Mock the orchestration layer
        with patch.object(client.orchestration_layer, 'start_audit') as mock_start_audit:
            mock_start_audit.return_value = Mock()  # Mock report panel
            
            # Simulate audit command processing
            query = f"audit {sample_solidity_contract}"
            parts = query.split()
            target = parts[1]
            
            report_panel = await client.orchestration_layer.start_audit({'target': target})
            
            # Verify audit was initiated
            mock_start_audit.assert_called_once_with({'target': target})
            assert report_panel is not None
    
    @pytest.mark.asyncio
    async def test_end_to_end_audit_workflow(self, console, sample_foundry_project):
        """Test complete end-to-end audit workflow."""
        # This test simulates a complete audit from start to finish
        
        # Initialize components
        orchestration = OrchestrationLayer(console)
        
        # Mock tool availability to avoid installation requirements
        with patch.object(orchestration.analysis_engine.slither_module, 'is_available', return_value=True), \
             patch.object(orchestration.analysis_engine.mythril_module, 'is_available', return_value=True), \
             patch.object(orchestration.analysis_engine.foundry_module, 'is_available', return_value=True):
            
            # Mock actual tool execution
            with patch.object(orchestration.analysis_engine.slither_module, 'run_analysis') as mock_slither, \
                 patch.object(orchestration.analysis_engine.mythril_module, 'run_analysis') as mock_mythril, \
                 patch.object(orchestration.analysis_engine.foundry_module, 'run_analysis') as mock_foundry:
                
                # Setup realistic mock returns
                mock_slither.return_value = [
                    {
                        'tool': 'slither',
                        'check': 'reentrancy-eth',
                        'description': 'Reentrancy in VulnerableContract.withdraw()',
                        'impact': 'High',
                        'confidence': 'High',
                        'elements': [{'name': 'withdraw'}],
                        'markdown': 'Reentrancy vulnerability found in withdraw function'
                    }
                ]
                
                mock_mythril.return_value = [
                    {
                        'tool': 'mythril',
                        'check': 'unchecked-send',
                        'description': 'Unchecked return value from external call',
                        'impact': 'Medium',
                        'confidence': 'High',
                        'swc_id': 'SWC-104'
                    }
                ]
                
                mock_foundry.return_value = [
                    {
                        'tool': 'foundry',
                        'check': 'high-gas-usage',
                        'description': 'Function withdraw has high gas usage: 150000',
                        'impact': 'Low',
                        'confidence': 'Medium',
                        'function': 'withdraw',
                        'gas_usage': 150000
                    }
                ]
                
                # Run the audit
                config = {'target': sample_foundry_project}
                report_panel = await orchestration.start_audit(config)
                
                # Verify the workflow completed successfully
                assert report_panel is not None
                
                # Verify all analysis modules were invoked
                mock_slither.assert_called_once()
                mock_mythril.assert_called_once()
                mock_foundry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self, console, sample_solidity_contract):
        """Test error handling throughout the audit workflow."""
        orchestration = OrchestrationLayer(console)
        
        # Mock one module to raise an exception
        with patch.object(orchestration.analysis_engine.slither_module, 'run_analysis') as mock_slither, \
             patch.object(orchestration.analysis_engine.mythril_module, 'run_analysis') as mock_mythril, \
             patch.object(orchestration.analysis_engine.foundry_module, 'run_analysis') as mock_foundry:
            
            # Setup one module to fail
            mock_slither.side_effect = Exception("Slither execution failed")
            mock_mythril.return_value = []
            mock_foundry.return_value = []
            
            # The workflow should handle the error gracefully
            config = {'target': sample_solidity_contract}
            report_panel = await orchestration.start_audit(config)
            
            # Verify the workflow completed despite the error
            assert report_panel is not None
            
            # Verify other modules were still called
            mock_mythril.assert_called_once()
            mock_foundry.assert_called_once()
    
    def test_report_generation_with_various_findings(self, console):
        """Test report generation with different types and severities of findings."""
        engine = AnalysisEngine(console)
        
        # Create analysis results with various finding types
        analysis_results = {
            'target': 'TestContract.sol',
            'total_findings': 10,
            'high_severity': 3,
            'medium_severity': 4,
            'low_severity': 3,
            'risk_score': 57,  # 3*10 + 4*5 + 3*1
            'findings': [
                {
                    'tool': 'slither',
                    'check': 'reentrancy-eth',
                    'description': 'Critical reentrancy vulnerability in withdraw function',
                    'impact': 'High',
                    'confidence': 'High'
                },
                {
                    'tool': 'mythril',
                    'check': 'integer-overflow',
                    'description': 'Integer overflow in arithmetic operation',
                    'impact': 'High',
                    'confidence': 'Medium'
                },
                {
                    'tool': 'custom',
                    'check': 'donation-attack',
                    'description': 'Contract vulnerable to donation attacks',
                    'impact': 'High',
                    'confidence': 'Medium'
                },
                {
                    'tool': 'foundry',
                    'check': 'test-failure',
                    'description': 'Invariant test failed during fuzzing',
                    'impact': 'Medium',
                    'confidence': 'High'
                }
            ],
            'tool_status': {
                'slither': True,
                'mythril': True,
                'foundry': True
            }
        }
        
        report_panel = engine.generate_detailed_report(analysis_results)
        
        # Verify report was generated successfully
        assert report_panel is not None
        assert hasattr(report_panel, 'renderable')
        
        # The report should indicate CRITICAL risk level (score >= 50)
        assert "CRITICAL" in str(report_panel.title) or "HIGH" in str(report_panel.title)


if __name__ == '__main__':
    pytest.main([__file__])

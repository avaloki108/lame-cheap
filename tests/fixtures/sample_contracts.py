"""Sample smart contracts for testing Web3AuditMCP."""

# Vulnerable contract with multiple security issues
VULNERABLE_CONTRACT = '''
pragma solidity ^0.8.0;

contract VulnerableContract {
    mapping(address => uint256) public balances;
    address public owner;
    bool private locked;
    
    constructor() {
        owner = msg.sender;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    modifier noReentrancy() {
        require(!locked, "Reentrant call");
        locked = true;
        _;
        locked = false;
    }
    
    // Vulnerable to reentrancy (missing noReentrancy modifier)
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // State change after external call - vulnerable!
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount;
    }
    
    // Vulnerable to donation attacks
    function getBalance() public view returns (uint256) {
        return address(this).balance;  // Should use internal accounting
    }
    
    // Vulnerable to front-running
    function bid() public payable {
        require(msg.value > getHighestBid(), "Bid too low");
        // Process bid...
    }
    
    function getHighestBid() public view returns (uint256) {
        return address(this).balance / 2;  // Simplified logic
    }
    
    // Missing access control
    function emergencyWithdraw() public {
        // Should have onlyOwner modifier!
        payable(msg.sender).transfer(address(this).balance);
    }
    
    // Dangerous use of tx.origin
    function authorize() public {
        require(tx.origin == owner, "Not authorized");  // Should use msg.sender
    }
    
    // Integer overflow potential (if using older Solidity)
    function add(uint256 a, uint256 b) public pure returns (uint256) {
        return a + b;  // Could overflow in older versions
    }
    
    // Unchecked external call
    function externalCall(address target, bytes calldata data) public onlyOwner {
        target.call(data);  // Return value not checked
    }
    
    // Deposit function
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    receive() external payable {
        deposit();
    }
}
'''

# Secure contract with proper patterns
SECURE_CONTRACT = '''
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract SecureContract is ReentrancyGuard, Ownable {
    mapping(address => uint256) private balances;
    uint256 private totalDeposits;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    
    constructor() {}
    
    function deposit() public payable nonReentrant {
        require(msg.value > 0, "Must deposit something");
        
        balances[msg.sender] += msg.value;
        totalDeposits += msg.value;
        
        emit Deposit(msg.sender, msg.value);
    }
    
    function withdraw(uint256 amount) public nonReentrant {
        require(amount > 0, "Must withdraw something");
        require(balances[msg.sender] >= amount, "Insufficient balance");
        require(address(this).balance >= amount, "Contract insufficient funds");
        
        // Checks-Effects-Interactions pattern
        balances[msg.sender] -= amount;
        totalDeposits -= amount;
        
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");
        
        emit Withdrawal(msg.sender, amount);
    }
    
    function getBalance(address user) public view returns (uint256) {
        return balances[user];  // Use internal accounting
    }
    
    function getTotalDeposits() public view returns (uint256) {
        return totalDeposits;  // Internal accounting, not address(this).balance
    }
    
    function emergencyWithdraw() public onlyOwner {
        uint256 balance = address(this).balance;
        (bool success, ) = payable(owner()).call{value: balance}("");
        require(success, "Emergency withdrawal failed");
    }
    
    function safeExternalCall(address target, bytes calldata data) 
        public 
        onlyOwner 
        returns (bool success, bytes memory returnData) 
    {
        (success, returnData) = target.call(data);
        // Return values are handled by caller
    }
}
'''

# Contract with gas optimization issues
GAS_INEFFICIENT_CONTRACT = '''
pragma solidity ^0.8.0;

contract GasInefficientContract {
    uint256[] public largeArray;
    mapping(address => uint256[]) public userArrays;
    string public longString;
    
    // Inefficient loop
    function sumArray() public view returns (uint256) {
        uint256 sum = 0;
        for (uint256 i = 0; i < largeArray.length; i++) {
            sum += largeArray[i];  // Expensive SLOAD in loop
        }
        return sum;
    }
    
    // Inefficient storage usage
    function addToArray(uint256 value) public {
        largeArray.push(value);
        userArrays[msg.sender].push(value);  // Duplicate storage
    }
    
    // Inefficient string operations
    function concatenateStrings(string memory a, string memory b) 
        public 
        pure 
        returns (string memory) 
    {
        return string(abi.encodePacked(a, b, a, b, a, b));  // Inefficient
    }
    
    // Unnecessary external calls
    function getBlockInfo() public view returns (uint256, uint256, address) {
        return (block.number, block.timestamp, block.coinbase);
    }
}
'''

# Contract with complex DeFi patterns
DEFI_CONTRACT = '''
pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract DeFiContract {
    IERC20 public token;
    mapping(address => uint256) public stakes;
    mapping(address => uint256) public rewards;
    uint256 public totalStaked;
    uint256 public rewardRate = 100; // rewards per block
    uint256 public lastUpdateBlock;
    
    constructor(address _token) {
        token = IERC20(_token);
        lastUpdateBlock = block.number;
    }
    
    modifier updateReward(address account) {
        if (totalStaked > 0) {
            uint256 blocksPassed = block.number - lastUpdateBlock;
            uint256 totalReward = blocksPassed * rewardRate;
            
            if (stakes[account] > 0) {
                rewards[account] += (stakes[account] * totalReward) / totalStaked;
            }
        }
        lastUpdateBlock = block.number;
        _;
    }
    
    // Potential issues: flash loan attacks, price manipulation
    function stake(uint256 amount) public updateReward(msg.sender) {
        require(amount > 0, "Cannot stake 0");
        
        // Vulnerable: external call before state change
        require(token.transferFrom(msg.sender, address(this), amount), "Transfer failed");
        
        stakes[msg.sender] += amount;
        totalStaked += amount;
    }
    
    function unstake(uint256 amount) public updateReward(msg.sender) {
        require(amount > 0, "Cannot unstake 0");
        require(stakes[msg.sender] >= amount, "Insufficient stake");
        
        stakes[msg.sender] -= amount;
        totalStaked -= amount;
        
        require(token.transfer(msg.sender, amount), "Transfer failed");
    }
    
    function claimRewards() public updateReward(msg.sender) {
        uint256 reward = rewards[msg.sender];
        require(reward > 0, "No rewards");
        
        rewards[msg.sender] = 0;
        
        // Potential reentrancy if token has callbacks
        require(token.transfer(msg.sender, reward), "Reward transfer failed");
    }
    
    // Price oracle manipulation vulnerability
    function getTokenPrice() public view returns (uint256) {
        return token.balanceOf(address(this)) * 1e18 / totalStaked;
    }
}
'''

# Test contract for Foundry
FOUNDRY_TEST_CONTRACT = '''
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "./VulnerableContract.sol";

contract VulnerableContractTest is Test {
    VulnerableContract public vulnerableContract;
    address public attacker;
    
    function setUp() public {
        vulnerableContract = new VulnerableContract();
        attacker = makeAddr("attacker");
        
        // Fund the contract
        vm.deal(address(vulnerableContract), 10 ether);
        vm.deal(attacker, 1 ether);
    }
    
    function testDeposit() public {
        uint256 depositAmount = 1 ether;
        
        vm.prank(attacker);
        vulnerableContract.deposit{value: depositAmount}();
        
        assertEq(vulnerableContract.balances(attacker), depositAmount);
    }
    
    function testWithdraw() public {
        // Setup
        vm.prank(attacker);
        vulnerableContract.deposit{value: 1 ether}();
        
        // Test withdrawal
        vm.prank(attacker);
        vulnerableContract.withdraw(0.5 ether);
        
        assertEq(vulnerableContract.balances(attacker), 0.5 ether);
    }
    
    // This test should fail due to reentrancy vulnerability
    function testReentrancyAttack() public {
        ReentrancyAttacker attackerContract = new ReentrancyAttacker(vulnerableContract);
        
        vm.deal(address(attackerContract), 1 ether);
        vm.deal(address(vulnerableContract), 10 ether);
        
        attackerContract.attack{value: 1 ether}();
        
        // This assertion should fail if reentrancy is possible
        assertLt(address(vulnerableContract).balance, 10 ether);
    }
    
    // Invariant: total balances should never exceed contract balance
    function invariant_balanceConsistency() public {
        // This invariant should be violated due to donation attacks
        assertTrue(vulnerableContract.getBalance() >= address(vulnerableContract).balance);
    }
    
    // Fuzz test for overflow
    function testFuzzAdd(uint256 a, uint256 b) public {
        vm.assume(a <= type(uint256).max - b);  // Prevent overflow
        
        uint256 result = vulnerableContract.add(a, b);
        assertEq(result, a + b);
    }
}

contract ReentrancyAttacker {
    VulnerableContract public target;
    uint256 public attackCount;
    
    constructor(VulnerableContract _target) {
        target = _target;
    }
    
    function attack() public payable {
        target.deposit{value: msg.value}();
        target.withdraw(msg.value);
    }
    
    receive() external payable {
        if (attackCount < 3 && address(target).balance >= msg.value) {
            attackCount++;
            target.withdraw(msg.value);
        }
    }
}
'''

# Contract configurations for different test scenarios
CONTRACT_CONFIGS = {
    'vulnerable': {
        'name': 'VulnerableContract',
        'code': VULNERABLE_CONTRACT,
        'expected_issues': [
            'reentrancy-eth',
            'donation-attack',
            'front-running',
            'missing-access-control',
            'tx-origin',
            'unchecked-send'
        ],
        'severity_distribution': {
            'high': 4,
            'medium': 2,
            'low': 1
        }
    },
    'secure': {
        'name': 'SecureContract',
        'code': SECURE_CONTRACT,
        'expected_issues': [],
        'severity_distribution': {
            'high': 0,
            'medium': 0,
            'low': 0
        }
    },
    'gas_inefficient': {
        'name': 'GasInefficientContract',
        'code': GAS_INEFFICIENT_CONTRACT,
        'expected_issues': [
            'high-gas-usage',
            'inefficient-loop',
            'storage-optimization'
        ],
        'severity_distribution': {
            'high': 0,
            'medium': 1,
            'low': 3
        }
    },
    'defi': {
        'name': 'DeFiContract',
        'code': DEFI_CONTRACT,
        'expected_issues': [
            'reentrancy-eth',
            'price-manipulation',
            'flash-loan-attack',
            'external-call-ordering'
        ],
        'severity_distribution': {
            'high': 3,
            'medium': 1,
            'low': 0
        }
    }
}

def get_contract(contract_type: str) -> dict:
    """Get contract configuration by type."""
    return CONTRACT_CONFIGS.get(contract_type, CONTRACT_CONFIGS['vulnerable'])

def create_contract_file(contract_type: str, output_path: str) -> str:
    """Create a contract file for testing."""
    config = get_contract(contract_type)
    
    with open(output_path, 'w') as f:
        f.write(config['code'])
    
    return output_path

# Web3AuditMCP 🛡️

**The most comprehensive smart contract auditing tool powered by local LLMs**

Web3AuditMCP combines the best features of Slither, Mythril, Foundry fuzzing, and Hardhat checks with an AI-powered orchestration layer for end-to-end security audits.

## ✨ Features

- **🔍 Static Analysis**: Slither integration for comprehensive code analysis
- **🧠 Symbolic Execution**: Mythril-powered deep vulnerability detection  
- **🎯 Fuzzing**: Foundry-based property testing and invariant checking
- **📋 Custom Checks**: Bug bounty checklist with 500+ vulnerability patterns
- **🤖 AI-Powered**: Local LLM integration for intelligent analysis
- **⚡ Quick Scans**: Fast vulnerability detection for rapid feedback
- **📊 Rich Reports**: Beautiful, detailed security analysis reports
- **🔧 Tool Management**: Automatic installation and configuration

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- Docker (optional)
- uv package manager

### Installation

```bash
# Clone the repository
git clone <repository_url>
cd Web3AuditMCP

# Install with uv
uv pip install -e .

# Or install with pip
pip install -e .
```

### Basic Usage

```bash
# Start the interactive client
web3audit-mcp

# Run a comprehensive audit
audit ./contracts/MyContract.sol

# Run a quick scan
quick ./contracts/MyContract.sol

# Audit an entire repository
audit https://github.com/user/defi-project

# Get help
help
```

## 🛠️ Architecture

Web3AuditMCP follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   TUI Client    │───▶│ Orchestration    │───▶│ Analysis Engine │
│                 │    │     Layer        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Configuration    │    │ Security        │
                       │    Manager       │    │   Modules       │
                       └──────────────────┘    └─────────────────┘
                                                        │
                        ┌───────────────────────────────┼───────────────────────────────┐
                        ▼                               ▼                               ▼
                ┌──────────────┐              ┌──────────────┐              ┌──────────────┐
                │   Slither    │              │   Mythril    │              │   Foundry    │
                │   Module     │              │   Module     │              │   Module     │
                └──────────────┘              └──────────────┘              └──────────────┘
```

### Core Components

- **TUI Client**: Rich terminal interface for user interaction
- **Orchestration Layer**: Coordinates analysis workflow and manages tool execution
- **Analysis Engine**: Processes findings and generates comprehensive reports
- **Security Modules**: Individual tool integrations (Slither, Mythril, Foundry)
- **Configuration Manager**: Handles settings, model parameters, and audit configurations

## 🔧 Configuration

### Model Configuration

Web3AuditMCP supports various Ollama models for AI-powered analysis:

```bash
# Select a model
model

# Configure model parameters
model-config
```

Recommended models:
- `qwen3-coder:30b` - Best for code analysis
- `gpt-oss:20b` - Good general purpose model
- `codellama:34b` - Strong code understanding

### Tool Configuration

The system automatically detects and installs security tools:

- **Slither**: Static analysis for Solidity
- **Mythril**: Symbolic execution engine
- **Foundry**: Testing and fuzzing framework

## 📋 Vulnerability Detection

Web3AuditMCP detects a comprehensive range of vulnerabilities:

### High Severity
- Reentrancy attacks
- Integer overflow/underflow
- Access control issues
- Unchecked external calls
- Donation attacks
- Price manipulation

### Medium Severity
- Front-running vulnerabilities
- Gas griefing attacks
- Timestamp dependence
- Weak randomness
- Signature malleability

### Low Severity
- Gas optimization issues
- Code quality problems
- Best practice violations
- Documentation issues

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
uv pip install -e ".[test]"

# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=web3audit_mcp
```

### Test Structure

```
tests/
├── unit/                 # Unit tests for individual components
│   ├── test_analysis_engine.py
│   ├── test_slither_module.py
│   └── test_mythril_module.py
├── integration/          # Integration tests for workflows
│   └── test_audit_workflow.py
└── fixtures/            # Test data and sample contracts
    └── sample_contracts.py
```

## 📊 Example Output

```
🛡️ Security Analysis Report - HIGH RISK

📊 Summary
┌─────────────────┬───────┬─────────────┐
│ Metric          │ Count │ Risk Level  │
├─────────────────┼───────┼─────────────┤
│ Total Findings  │ 8     │             │
│ 🔴 Critical     │ 3     │             │
│ 🟡 Medium       │ 3     │             │
│ 🟢 Low          │ 2     │             │
│ Risk Score      │ 41    │ HIGH        │
└─────────────────┴───────┴─────────────┘

⚠️ Critical Findings (Top 5)
┌────────┬──────────────────────┬────────────────────────────────────────┬────────┐
│ Tool   │ Check                │ Description                            │ Impact │
├────────┼──────────────────────┼────────────────────────────────────────┼────────┤
│ Slither│ reentrancy-eth       │ Reentrancy vulnerability in withdraw  │ High   │
│ Mythril│ integer-overflow     │ Integer overflow in arithmetic op     │ High   │
│ Custom │ donation-attack      │ Contract vulnerable to donation attacks│ High   │
│ Foundry│ invariant-violation  │ Balance invariant violated in fuzzing │ Medium │
└────────┴──────────────────────┴────────────────────────────────────────┴────────┘
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup development environment
git clone <repository_url>
cd Web3AuditMCP

# Install in development mode
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Slither](https://github.com/crytic/slither) - Static analysis framework
- [Mythril](https://github.com/ConsenSys/mythril) - Symbolic execution engine  
- [Foundry](https://github.com/foundry-rs/foundry) - Testing and fuzzing toolkit
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal interfaces

## 🔗 Links

- [Documentation](docs/)
- [Bug Reports](https://github.com/user/web3audit-mcp/issues)
- [Feature Requests](https://github.com/user/web3audit-mcp/discussions)
- [Security Policy](SECURITY.md)

---

**Built with ❤️ for the Web3 security community**

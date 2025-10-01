# Web3AuditMCP 🛡️

**Enhanced Smart Contract Security Auditing Platform**

Web3AuditMCP is a comprehensive, AI-powered smart contract security auditing platform that combines the best features of Slither, Mythril, Foundry fuzzing, and Hardhat checks with advanced multi-agent orchestration and LLM-enhanced analysis.

## ✨ Features

### 🤖 Multi-Agent Security Analysis
- **Vulnerability Detection Agent**: Comprehensive static and dynamic analysis
- **Exploit Scenario Agent**: Generates detailed attack vectors and impact assessments  
- **Fix Recommendation Agent**: Provides actionable remediation guidance with code examples

### 🧠 AI-Enhanced Analysis
- **LLM Integration**: Powered by Ollama with support for Qwen2.5-Coder, Llama3.1, and CodeLlama
- **Intelligent Findings Enhancement**: AI-powered severity assessment and false positive reduction
- **Automated Remediation**: Context-aware fix suggestions with implementation examples

### 🔧 Comprehensive Tool Integration
- **Slither**: Advanced static analysis with custom detectors
- **Mythril**: Symbolic execution and vulnerability detection
- **Foundry**: Fuzzing and property-based testing
- **Custom Analyzers**: Pattern-based vulnerability detection

### 📊 Advanced Reporting
- **Rich Terminal Interface**: Beautiful, interactive command-line experience
- **Detailed Reports**: Comprehensive findings with exploit scenarios and fixes
- **Multiple Export Formats**: JSON, Markdown, PDF support
- **Risk Scoring**: Intelligent risk assessment and prioritization

### 🚀 Enterprise Features
- **Docker Support**: Containerized deployment with monitoring stack
- **Configuration Management**: Flexible, profile-based configuration
- **Audit History**: Persistent storage and analysis tracking
- **Parallel Execution**: Multi-threaded analysis for faster results

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (Python 3.12 recommended)
- **Node.js 18+** (for some security tools)
- **Git** (for repository analysis)
- **Docker** (optional, for containerized deployment)

### Installation

#### Option 1: Automated Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/web3audit-mcp.git
cd web3audit-mcp

# Run the installation wizard
python install.py
```

The installer will:
- ✅ Check system requirements
- 📦 Install Python dependencies with uv/pip
- 🛠️ Install security tools (Slither, Mythril, Foundry)
- 🧠 Setup Ollama and download AI models
- ⚙️ Create default configuration

#### Option 2: Manual Installation

```bash
# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .

# Install security tools
pip install slither-analyzer mythril

# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install and setup Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5-coder:7b
ollama pull llama3.1:8b
```

#### Option 3: Docker Deployment

```bash
# Clone and start with Docker Compose
git clone https://github.com/your-org/web3audit-mcp.git
cd web3audit-mcp

# Start the full stack
docker-compose up -d

# Access the web interface
open http://localhost:8000
```

### First Audit

```bash
# Start the interactive client
web3audit-mcp

# Or run directly
web3audit-mcp audit ./my-contract/
web3audit-mcp quick MyContract.sol
```

## 📖 Usage Guide

### Interactive Client

The Web3AuditMCP client provides a rich, interactive terminal interface:

```bash
web3audit-mcp
```

**Available Commands:**
- `audit <target>` - Run comprehensive security audit
- `quick <target>` - Run quick vulnerability scan  
- `status` - Show system and tool status
- `config [action]` - Manage configuration
- `model [action]` - Manage AI models
- `history` - Show command history
- `export [format]` - Export audit results
- `help` - Show help information

### Command Line Interface

```bash
# Comprehensive audit
web3audit-mcp audit ./contracts/

# Quick scan
web3audit-mcp quick MyContract.sol

# Audit with specific configuration
web3audit-mcp audit ./project/ --config production

# Export results
web3audit-mcp export --format markdown --output report.md
```

### Supported Targets

- **Solidity Files**: `MyContract.sol`
- **Project Directories**: `./contracts/`, `./src/`
- **Git Repositories**: `https://github.com/user/project.git`
- **Foundry Projects**: Auto-detected `foundry.toml`
- **Hardhat Projects**: Auto-detected `hardhat.config.js`

## ⚙️ Configuration

### Configuration File

Web3AuditMCP uses TOML configuration files located at `~/.web3audit/config.toml`:

```toml
[config]
version = "1.0.0"

[model]
default_model = "qwen2.5-coder:7b"
temperature = 0.7
top_p = 0.9
max_tokens = 2000

[tools]
slither_enabled = true
mythril_enabled = true
foundry_enabled = true

[audit]
parallel_execution = true
detailed_reports = true
export_format = "json"

[output]
console_style = "rich"
log_level = "INFO"
```

### Environment Variables

```bash
export WEB3AUDIT_CONFIG_PATH="/path/to/config.toml"
export WEB3AUDIT_LOG_LEVEL="DEBUG"
export OLLAMA_HOST="localhost:11434"
```

### Model Configuration

```bash
# List available models
web3audit-mcp model list

# Download new model
web3audit-mcp model pull qwen2.5-coder:14b

# Set default model
web3audit-mcp model select
```

## 🔍 Analysis Capabilities

### Vulnerability Detection

**Static Analysis:**
- Reentrancy vulnerabilities
- Access control issues
- Integer overflow/underflow
- Unchecked external calls
- Timestamp dependence
- tx.origin usage
- Denial of Service patterns

**Dynamic Analysis:**
- Symbolic execution with Mythril
- Fuzzing with Foundry
- Property-based testing
- State space exploration

**AI-Enhanced Analysis:**
- Severity assessment refinement
- False positive reduction
- Context-aware recommendations
- Exploit scenario generation

### Security Checklist Integration

Web3AuditMCP includes a comprehensive security checklist covering:

- **Access Management (AM)**: 15+ checks
- **Arithmetic (AR)**: 10+ checks  
- **Assembly Usage (AU)**: 8+ checks
- **Best Practices (BP)**: 20+ checks
- **Centralization (CE)**: 12+ checks
- **Gas Optimization (GO)**: 15+ checks
- **And many more...**

## 📊 Reporting

### Report Formats

**Terminal Output:**
- Rich, colorized tables and panels
- Interactive progress indicators
- Real-time analysis updates

**Export Formats:**
- **JSON**: Machine-readable results
- **Markdown**: Human-readable reports
- **PDF**: Professional audit reports (coming soon)

### Sample Report Structure

```
🛡️ Web3 Security Audit Report - HIGH RISK

📊 Audit Summary
┌─────────────────┬───────┬────────┐
│ Metric          │ Value │ Status │
├─────────────────┼───────┼────────┤
│ Total Findings  │    12 │   📋   │
│ Critical        │     2 │   🔴   │
│ High            │     4 │   🟡   │
│ Medium          │     5 │   🟠   │
│ Low             │     1 │   🟢   │
│ Risk Score      │    45 │  HIGH  │
└─────────────────┴───────┴────────┘

🔍 Top Security Findings
┌──────────┬────────────┬─────────────────────────┬────────────┐
│ Severity │ Tool       │ Finding                 │ Confidence │
├──────────┼────────────┼─────────────────────────┼────────────┤
│ CRITICAL │ slither    │ Reentrancy in withdraw  │       0.95 │
│ HIGH     │ mythril    │ Integer overflow        │       0.87 │
│ HIGH     │ custom     │ Unchecked external call │       0.82 │
└──────────┴────────────┴─────────────────────────┴────────────┘

🎯 Key Recommendations:
• 🚨 IMMEDIATE ACTION REQUIRED: Critical vulnerabilities found
• ⚠️ High-severity issues require prompt attention
• 🧠 LLM-generated remediation guidance available
```

## 🐳 Docker Deployment

### Production Deployment

```bash
# Clone repository
git clone https://github.com/your-org/web3audit-mcp.git
cd web3audit-mcp

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Services Included

- **Web3AuditMCP**: Main application
- **PostgreSQL**: Audit history storage
- **Redis**: Caching and sessions
- **Nginx**: Reverse proxy and SSL
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards
- **Loki**: Log aggregation

### Monitoring

Access monitoring dashboards:
- **Application**: http://localhost:8000
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

## 🧪 Development

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/web3audit-mcp.git
cd web3audit-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\\Scripts\\activate` on Windows

# Install in development mode
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/
```

### Project Structure

```
web3audit-mcp/
├── web3audit_mcp/           # Main package
│   ├── agents/              # Multi-agent system
│   ├── core/                # Core adapters and utilities
│   ├── llm/                 # LLM integration
│   ├── modules/             # Security analysis modules
│   ├── config/              # Configuration management
│   └── tools/               # Tool integrations
├── tests/                   # Test suite
├── docker/                  # Docker configuration
├── docs/                    # Documentation
└── examples/                # Example contracts and configs
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=web3audit_mcp

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 🔒 Security Considerations

### Tool Security
- All analysis tools run in isolated environments
- No network access during analysis (except for model inference)
- Temporary files are securely cleaned up
- Input validation and sanitization

### AI Model Security
- Local LLM execution (no data sent to external services)
- Configurable model selection and parameters
- Analysis results are not used for model training
- Sensitive code patterns are filtered from LLM context

### Data Privacy
- All analysis data stays local
- Optional encrypted storage for audit history
- Configurable data retention policies
- GDPR-compliant data handling

## 📚 Documentation

- **[Installation Guide](docs/installation.md)**: Detailed setup instructions
- **[Configuration Reference](docs/configuration.md)**: Complete configuration options
- **[API Documentation](docs/api.md)**: Programmatic interface
- **[Security Checklist](docs/checklist.md)**: Complete vulnerability checklist
- **[Contributing Guide](docs/contributing.md)**: Development guidelines

## 🤝 Community

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and ideas
- **Discord**: Real-time chat and support
- **Twitter**: Updates and announcements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Web3AuditMCP builds upon the excellent work of:

- **[Slither](https://github.com/crytic/slither)** - Static analysis framework
- **[Mythril](https://github.com/ConsenSys/mythril)** - Symbolic execution engine
- **[Foundry](https://github.com/foundry-rs/foundry)** - Ethereum development toolkit
- **[Ollama](https://ollama.ai/)** - Local LLM inference
- **[Rich](https://github.com/Textualize/rich)** - Terminal formatting

## 🚀 Roadmap

### v1.1 (Next Release)
- [ ] Web-based dashboard
- [ ] CI/CD integration plugins
- [ ] Advanced fuzzing strategies
- [ ] Multi-chain support

### v1.2 (Future)
- [ ] Machine learning-based vulnerability detection
- [ ] Automated fix generation
- [ ] Integration with bug bounty platforms
- [ ] Advanced visualization tools

---

**Made with ❤️ by the Web3AuditMCP Team**

*Securing the decentralized future, one smart contract at a time.*

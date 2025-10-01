# Web3AuditMCP - Enhanced Smart Contract Security Auditing Platform
# Multi-stage Docker build for optimized production deployment

# Stage 1: Base system with dependencies
FROM ubuntu:22.04 as base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    nodejs \
    npm \
    git \
    curl \
    wget \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Create python3 symlink
RUN ln -sf /usr/bin/python3.12 /usr/bin/python3
RUN ln -sf /usr/bin/python3.12 /usr/bin/python

# Install uv for fast Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Stage 2: Security tools installation
FROM base as tools

# Install Foundry
RUN curl -L https://foundry.paradigm.xyz | bash
ENV PATH="/root/.foundry/bin:$PATH"
RUN foundryup

# Install Slither
RUN python3 -m pip install --no-cache-dir slither-analyzer

# Install Mythril
RUN python3 -m pip install --no-cache-dir mythril

# Install additional security tools
RUN python3 -m pip install --no-cache-dir \
    solc-select \
    crytic-compile \
    echidna-parade

# Install Solidity compiler versions
RUN solc-select install 0.8.19 && \
    solc-select install 0.8.20 && \
    solc-select install 0.8.21 && \
    solc-select use 0.8.20

# Stage 3: Ollama installation
FROM tools as ollama-stage

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Create ollama user and directories
RUN useradd -m -s /bin/bash ollama
RUN mkdir -p /usr/share/ollama/.ollama
RUN chown -R ollama:ollama /usr/share/ollama/.ollama

# Stage 4: Application setup
FROM ollama-stage as app

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies using uv
RUN uv pip install --system -e .

# Create non-root user for security
RUN useradd -m -s /bin/bash web3audit && \
    chown -R web3audit:web3audit /app

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/config && \
    chown -R web3audit:web3audit /app/data /app/logs /app/config

# Copy configuration files
COPY docker/config/ /app/config/
COPY docker/scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh

# Stage 5: Production image
FROM app as production

# Install supervisor for process management
RUN apt-get update && apt-get install -y supervisor && \
    rm -rf /var/lib/apt/lists/*

# Copy supervisor configuration
COPY docker/supervisor/ /etc/supervisor/conf.d/

# Create startup script
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting Web3AuditMCP..."

# Start Ollama service in background
echo "Starting Ollama service..."
su - ollama -c "ollama serve" &
sleep 5

# Download default models if not present
echo "Checking AI models..."
if ! ollama list | grep -q "qwen2.5-coder:7b"; then
    echo "Downloading qwen2.5-coder:7b model..."
    ollama pull qwen2.5-coder:7b
fi

if ! ollama list | grep -q "llama3.1:8b"; then
    echo "Downloading llama3.1:8b model..."
    ollama pull llama3.1:8b
fi

# Verify security tools
echo "Verifying security tools..."
slither --version || echo "⚠️ Slither not available"
myth version || echo "⚠️ Mythril not available"
forge --version || echo "⚠️ Foundry not available"

echo "✅ Web3AuditMCP ready!"

# Start the main application
exec "$@"
EOF

RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

# Expose ports
EXPOSE 8000 11434

# Set user
USER web3audit

# Default command
ENTRYPOINT ["/app/start.sh"]
CMD ["web3audit-mcp", "--host", "0.0.0.0", "--port", "8000"]

# Labels for metadata
LABEL maintainer="Web3AuditMCP Team"
LABEL version="1.0.0"
LABEL description="Enhanced Smart Contract Security Auditing Platform"
LABEL org.opencontainers.image.source="https://github.com/your-org/web3audit-mcp"

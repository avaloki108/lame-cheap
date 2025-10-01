#!/usr/bin/env python
"""Command-line interface for Web3AuditMCP."""

from .client import app

def run_cli():
    """Run the Web3AuditMCP command-line interface."""
    app()

if __name__ == "__main__":
    run_cli()


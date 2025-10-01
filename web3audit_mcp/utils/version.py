"""Version checking for Web3AuditMCP."""
import httpx
from rich.console import Console
from ... import __version__

async def check_for_updates(console: Console):
    """Check for updates to the Web3AuditMCP package."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://pypi.org/pypi/web3audit-mcp/json")
            if response.status_code == 200:
                latest_version = response.json()["info"]["version"]
                if latest_version > __version__:
                    console.print(f"[yellow]A new version of Web3AuditMCP is available: {latest_version}[/yellow]")
                    console.print("[yellow]Upgrade with: pip install --upgrade web3audit-mcp[/yellow]")
    except Exception:
        pass  # Ignore errors


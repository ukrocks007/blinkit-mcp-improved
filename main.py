import sys
import subprocess
from src.server import mcp, SERVE_SSE


def ensure_browsers_installed():
    """
    Ensure Playwright browsers are installed.
    This is critical for the MCP server to function correctly,
    especially when running from a fresh .mcpb install.
    """
    try:
        # We use sys.executable to ensure we use the same python environment
        subprocess.run(
            [sys.executable, "-m", "playwright", "install"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to install Playwright browsers: {e}")
    except Exception as e:
        print(f"Warning: Unexpected error checking browsers: {e}")


def main():
    ensure_browsers_installed()
    # Run the MCP server
    if SERVE_SSE:
        mcp.run(transport="sse")
    else:
        mcp.run()


if __name__ == "__main__":
    main()

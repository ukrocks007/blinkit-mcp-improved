#!/bin/bash

# Add common install locations for uv to PATH
export PATH=$HOME/.local/bin:$HOME/.cargo/bin:$PATH

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# detailed logging for debugging if it still fails
if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found. Installing..." >&2
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Re-add to PATH in case it wasn't there before (redundant but safe)
    export PATH=$HOME/.local/bin:$HOME/.cargo/bin:$PATH
else
    echo "uv found at: $(command -v uv)" >&2
fi

# Ensure dependencies are installed
echo "Syncing dependencies..." >&2
uv sync --frozen

echo "Starting Blinkit MCP..." >&2
exec uv run main.py

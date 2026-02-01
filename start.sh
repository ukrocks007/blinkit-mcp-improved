#!/bin/bash

# Blinkit MCP Server - Node.js Startup Script

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Check if Node.js is installed
if ! command -v node > /dev/null 2>&1; then
    echo "Error: Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/" >&2
    exit 1
fi

echo "Node.js found: $(node --version)" >&2

# Navigate to src directory
cd src

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..." >&2
    npm install
else
    echo "Dependencies already installed." >&2
fi

# Check for Playwright browsers
if ! npx playwright list-files chromium > /dev/null 2>&1; then
    echo "Installing Playwright Chromium..." >&2
    npx playwright install chromium
else
    echo "Playwright Chromium already installed." >&2
fi

echo "Starting Blinkit MCP Server..." >&2
exec node index.js

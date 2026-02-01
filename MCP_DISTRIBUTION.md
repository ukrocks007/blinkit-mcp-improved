# MCP Server Distribution & Installation Guide

## Overview

This guide explains how to distribute and install MCP servers for maximum compatibility across different clients (Claude Desktop, VS Code, OpenClaw, etc.).

## Standard MCP Installation Methods

### 1. NPM Package (Recommended for Node.js)

**Best for:** Wide distribution, easy updates, standard Node.js ecosystem

#### Publishing Your Server

```bash
# 1. Ensure you're logged into npm
npm login

# 2. Publish from src/ directory
cd src
npm publish --access public
```

#### User Installation

```bash
# One-time global install
npm install -g @ukrocks007/blinkit-mcp

# Or use npx (no install needed)
npx -y @ukrocks007/blinkit-mcp
```

#### Configuration (All Clients)

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "blinkit": {
      "command": "npx",
      "args": ["-y", "@ukrocks007/blinkit-mcp"]
    }
  }
}
```

**VS Code** (`settings.json`):
```json
{
  "github.copilot.chat.mcp.servers": {
    "blinkit": {
      "command": "npx",
      "args": ["-y", "@ukrocks007/blinkit-mcp"]
    }
  }
}
```

**Advantages:**
- ✅ No manual path configuration
- ✅ Automatic updates via npm
- ✅ Works on any OS
- ✅ Standard Node.js distribution

---

### 2. Git Clone + Manual Config (Current Method)

**Best for:** Development, custom modifications

#### Installation

```bash
git clone https://github.com/ukrocks007/blinkit-mcp-improved.git
cd blinkit-mcp-improved/src
npm install
npx playwright install chromium
```

#### Configuration

```json
{
  "mcpServers": {
    "blinkit": {
      "command": "node",
      "args": ["/absolute/path/to/blinkit-mcp-improved/src/index.js"]
    }
  }
}
```

**Advantages:**
- ✅ Full source code access
- ✅ Easy to modify
- ✅ No npm account needed

**Disadvantages:**
- ❌ Manual path configuration
- ❌ Manual updates
- ❌ Path differs per user

---

### 3. MCP Registry (Future Standard)

**Best for:** One-click installs, discoverability

Anthropic is building an official MCP registry. Your server needs:

**manifest.json** (already created):
```json
{
  "manifest_version": "0.3",
  "name": "blinkit-mcp",
  "version": "2.0.0",
  "server": {
    "type": "node",
    "entry_point": "src/index.js"
  }
}
```

Once registry is live, users can install with:
```bash
mcp install blinkit-mcp
```

---

### 4. Docker Container (For Complex Dependencies)

**Best for:** Isolated environments, complex dependencies

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY src/ .
RUN npm install
RUN npx playwright install --with-deps chromium
CMD ["node", "index.js"]
```

```json
{
  "mcpServers": {
    "blinkit": {
      "command": "docker",
      "args": ["run", "-i", "ukrocks007/blinkit-mcp:2.0.0"]
    }
  }
}
```

---

## Recommended Distribution Strategy

### For Blinkit MCP Server:

**Primary:** NPM Package
```bash
npm install -g @ukrocks007/blinkit-mcp
```

**Alternative:** Direct npx (no install)
```bash
npx @ukrocks007/blinkit-mcp
```

**Fallback:** Git clone for developers
```bash
git clone https://github.com/ukrocks007/blinkit-mcp-improved.git
```

---

## Client Compatibility Matrix

| Client | NPM Package | Git Clone | MCP Registry | Docker |
|--------|-------------|-----------|--------------|--------|
| Claude Desktop | ✅ Best | ✅ Works | 🔜 Coming | ✅ Works |
| VS Code Copilot | ✅ Best | ✅ Works | ❓ TBD | ✅ Works |
| OpenClaw/Gemini | ✅ Best | ✅ Works | ❓ TBD | ✅ Works |
| Cline | ✅ Best | ✅ Works | ❓ TBD | ✅ Works |
| Continue.dev | ✅ Best | ✅ Works | ❓ TBD | ✅ Works |

---

## Publishing Checklist

Before publishing to npm:

- [x] Update `package.json` with proper metadata
- [x] Add `bin` field for CLI execution
- [x] Set `engines.node` requirement
- [x] Include `files` array (what to publish)
- [x] Add shebang to index.js: `#!/usr/bin/env node`
- [ ] Test installation: `npm link` then use it
- [ ] Publish: `npm publish --access public`
- [ ] Test npx: `npx @ukrocks007/blinkit-mcp`

---

## Next Steps

### 1. Add Shebang to index.js

```javascript
#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
// ... rest of code
```

### 2. Test Locally

```bash
cd src
npm link
npx blinkit-mcp  # Should work
```

### 3. Publish to npm

```bash
npm publish --access public
```

### 4. Update Documentation

Add npm install instructions to README.md

---

## Standard MCP Server Requirements

All MCP servers should:

1. **Support stdio transport** (stdin/stdout)
2. **Provide clear tool schemas** (input/output types)
3. **Include manifest.json** (for registries)
4. **Document configuration** (for each client)
5. **Handle errors gracefully** (informative messages)
6. **Persist state if needed** (cookies, sessions)
7. **Be cross-platform** (Windows, macOS, Linux)

Your Blinkit MCP server checks all these boxes! ✅

---

## Summary

**Most Compatible Method:** NPM Package with npx execution

**User Experience:**
```bash
# No installation needed!
npx @ukrocks007/blinkit-mcp
```

**Config (any client):**
```json
{
  "mcpServers": {
    "blinkit": {
      "command": "npx",
      "args": ["-y", "@ukrocks007/blinkit-mcp"]
    }
  }
}
```

This works across Claude Desktop, VS Code, OpenClaw, and any MCP-compatible client.

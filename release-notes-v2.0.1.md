# v2.0.1 - MCP Inspector Compatibility Fix

## 🐛 Bug Fix Release

Fixed input field display in MCP Inspector by using the stable `Server` API instead of `McpServer`.

---

## 🔧 What's Fixed

### MCP Inspector Input Fields
- ✅ **Input fields now display correctly** in MCP Inspector
- ✅ All tool parameters (phoneNumber, otp, query, etc.) are visible
- ✅ Reverted from experimental `McpServer` to stable `Server` API
- ✅ Proper `inputSchema` format recognized by Inspector UI

### Documentation Added
- ✅ Added `MCP_DISTRIBUTION.md` - Complete guide on distribution methods
- ✅ NPM publishing instructions
- ✅ Multi-client compatibility matrix

---

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/ukrocks007/blinkit-mcp-improved.git
cd blinkit-mcp-improved/src

# Install dependencies
npm install
npx playwright install chromium

# Run server
node index.js
```

## 🔧 Claude Desktop Integration

Add to `claude_desktop_config.json`:

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

## 🧪 Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector node /absolute/path/to/blinkit-mcp-improved/src/index.js
```

All input fields will now display correctly! ✨

---

## 🛠️ Technical Changes

```diff
- import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
+ import { Server } from "@modelcontextprotocol/sdk/server/index.js";
+ import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

- this.server.registerTool(name, { inputSchema }, callback)
+ this.server.setRequestHandler(ListToolsRequestSchema, () => ({ tools: [...] }))
+ this.server.setRequestHandler(CallToolRequestSchema, (request) => {...})
```

---

## ✅ Verified Working

- ✅ All 7 tools functional
- ✅ Input fields visible in MCP Inspector
- ✅ Test client passing
- ✅ Search optimization (60-75% faster)
- ✅ COD checkout with proper button enablement
- ✅ Cart scoping fixes

---

## 📚 Documentation

- **README.md** - User installation guide
- **API_IMPLEMENTATION.md** - Technical documentation  
- **MCP_DISTRIBUTION.md** - Distribution & publishing guide (NEW)
- **CHANGELOG.md** - Complete version history

---

## 🚀 All Features from v2.0.0

This release maintains all features from v2.0.0 Node.js migration:
- 7 MCP tools (login, verify_otp, search_products, add_to_cart, check_cart, get_addresses, place_order_cod)
- 60-75% faster product search
- Robust COD checkout flow
- Cart scoping improvements
- Comprehensive logging

---

**Full Changelog**: [v2.0.0...v2.0.1](https://github.com/ukrocks007/blinkit-mcp-improved/compare/v2.0.0...v2.0.1)

# v2.0.0 - Node.js Migration 🚀

## 🎯 Complete Rewrite: Python → Node.js

This is a **major release** featuring a complete migration from Python to Node.js, bringing significant performance improvements and better maintainability.

---

## 🚨 BREAKING CHANGES

- **Requires Node.js 18+** instead of Python 3.8+
- **Tool names changed**: `enter_otp` → `verify_otp`, `search` → `search_products`
- **UPI payments removed**: Only COD (Cash on Delivery) supported in v2.0.0
- **New installation**: `npm install` instead of `uv sync`

---

## ✨ What's New

### 7 MCP Tools
1. **login** - Start authentication with phone number
2. **verify_otp** - Complete login with OTP code  
3. **search_products** - Fast product search with variants
4. **add_to_cart** - Add items by index
5. **check_cart** - View cart contents
6. **get_addresses** - List delivery addresses
7. **place_order_cod** - Complete COD checkout

### Performance Improvements
- ⚡ **60-75% faster search** via Promise.race optimization
- ⚡ **Reduced wait times**: 2s → 0.5s for DOM stability
- ⚡ **Smart polling**: Early exit on button enablement

### Robust Checkout
- ✅ Cash panel expansion with proper waits
- ✅ COD option selection with visibility checks
- ✅ Pay Now enablement polling (up to 10s)
- ✅ Error detection for COD restrictions
- ✅ Address validation before proceeding

### Better Selectors
- Tailwind CSS support (`tw-font-semibold`, `tw-text-300`)
- Styled-components partial matching
- Multi-layer fallback strategies
- Structural attributes (tabindex, role, id)

---

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/ukrocks007/blinkit-mcp-improved.git
cd blinkit-mcp-improved

# Install dependencies
cd src
npm install

# Install Playwright browser
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

## 🧪 Testing

```bash
cd src
node test_client.js
```

All 7 tools verified and working! ✅

---

## 📖 Documentation

- [README.md](https://github.com/ukrocks007/blinkit-mcp-improved/blob/main/README.md) - Complete user guide
- [API_IMPLEMENTATION.md](https://github.com/ukrocks007/blinkit-mcp-improved/blob/main/API_IMPLEMENTATION.md) - Technical details
- [CHANGELOG.md](https://github.com/ukrocks007/blinkit-mcp-improved/blob/main/CHANGELOG.md) - Full changelog
- [CONTRIBUTING.md](https://github.com/ukrocks007/blinkit-mcp-improved/blob/main/CONTRIBUTING.md) - Developer guide

---

## ⚠️ Known Limitations

- **COD only**: UPI/Card payments not yet implemented
- **Manual OTP**: User must enter OTP from phone
- **Single session**: One browser instance per server
- **India-specific**: Phone numbers and addresses

---

## 🔮 Coming Soon

- UPI payment support
- Card payment support
- Cart modification (remove/update)
- Order history
- Search filters

---

## 🙏 Credits

Built with:
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Playwright](https://playwright.dev/)
- [Node.js](https://nodejs.org/)

---

**Full Changelog**: [v1.0.0...v2.0.0](https://github.com/ukrocks007/blinkit-mcp-improved/compare/v1.0.0...v2.0.0)
